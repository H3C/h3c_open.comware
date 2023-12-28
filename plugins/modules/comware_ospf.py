#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_ospf
short_description: Manage ospf
description:
    - Manage ospf
version_added: 1.0.0
author: hanyangyang (@hanyangyang)
notes:

options:
    ospfname:
        description:
            - Instance name.(1~65535)
        required: true
        type: str
    routerid:
        description:
            - Router identifier.
        required: false
        type: str
    import_route:
        description:
            - Import route type
        required: false
        choices: ['bgp', 'direct', 'isis', 'ospf', 'rip', 'static']
        type: str
    area:
        description:
            - Area ID
        required: false
        type: str
    areatype:
        description:
            - Area type
        required: false
        choices: ['NSSA', 'Stub']
        type: str
    networkaddr:
        description:
            -  OSPF network  address
        required: false
        type: str
    wildcardmask:
        description:
            - wild ip address mask
        required: false
        type: str
    bandwidth:
        description:
            - Configure the bandwidth reference value by which link overhead is calculated(1~4294967)
        required: false
        type: str
    lsa_generation_max:
        description:
            - Maximum time interval between OSPF LSA regenerations(1~60s)
        required: false
        type: str
    lsa_generation_min:
        description:
            - Minimum time interval between OSPF LSA regenerations(10~60000ms)
        required: false
        type: str
    lsa_generation_inc:
        description:
            - Interval penalty increment for OSPF LSA regeneration(10~60000ms)
        required: false
        type: str
    lsa_arrival:
        description:
            - Configure the minimum time interval for repeat arrival of OSPF LSA(0~60000ms)
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'default']
        type: str

"""
EXAMPLES = """

      - name: Basic Ethernet config1
        h3c_open.comware.comware_ospf:
          ospfname: 4
          area: 2.2.2.2
          areatype: NSSA
          lsa_generation_max: 20
          lsa_generation_min: 20
          lsa_generation_inc: 20
        register: results

      - name: Basic Ethernet config2
        h3c_open.comware.comware_ospf:
          ospfname: 5
          area: 2.2.2.2
          areatype: Stub
          lsa_generation_max: 20
          lsa_generation_min: 20
          lsa_generation_inc: 20
        register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.ospf import Ospf
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ospfname=dict(required=True, type='str'),
            routerid=dict(type='str'),
            import_route=dict(choices=['bgp', 'direct', 'isis',
                                       'ospf', 'rip', 'static'],
                              type='str'),
            area=dict(required=False, type='str'),
            networkaddr=dict(type='str'),
            wildcardmask=dict(type='str'),
            areatype=dict(choices=['NSSA', 'Stub'], type='str'),
            bandwidth=dict(type='str'),
            lsa_generation_max=dict(type='str'),
            lsa_generation_min=dict(type='str'),
            lsa_generation_inc=dict(type='str'),
            lsa_arrival=dict(type='str'),
            state=dict(choices=['present', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)

    state = module.params['state']
    ospfname = module.params['ospfname']
    area = module.params['area']
    areatype = module.params['areatype']
    routerid = module.params['routerid']
    lsa_generation_max = module.params['lsa_generation_max']
    lsa_generation_min = module.params['lsa_generation_min']
    lsa_generation_inc = module.params['lsa_generation_inc']
    lsa_arrival = module.params['lsa_arrival']
    bandwidth = module.params['bandwidth']
    import_route = module.params['import_route']
    networkaddr = module.params['networkaddr']
    wildcardmask = module.params['wildcardmask']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if area == '0.0.0.0' and areatype:
        safe_fail(module, msg='OSPF backbone invalid for any options.')

    if area is None and networkaddr is not None:
        safe_fail(module, msg='networkaddr and wildcardmask needs to be configured in the area')

    if networkaddr is None and wildcardmask is not None:
        safe_fail(module, msg='networkaddr and wildcardmask need to be provided together')

    if networkaddr is not None and wildcardmask is None:
        safe_fail(module, msg='networkaddr and wildcardmask need to be provided together')

    ospf = None
    try:
        ospf = Ospf(device, ospfname, area)
    except PYCW7Error as exe:
        safe_fail(module, descr='there is problem in setting ospf config',
                  msg=str(exe))

    try:
        ospf.param_check(**proposed)
    except PYCW7Error as exe:
        safe_fail(module, descr='There was problem with the supplied parameters.',
                  msg=str(exe))

    existing = None
    try:
        existing = ospf.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting existing config.')

    proposed_lsa = dict(ospfname=ospfname,
                        lsa_generation_max=lsa_generation_max,
                        lsa_arrival=lsa_arrival,
                        lsa_generation_min=lsa_generation_min,
                        lsa_generation_inc=lsa_generation_inc,
                        bandwidth=bandwidth)

    if state == 'present':
        if ospfname:
            proposed_ospf = dict(ospfname=ospfname)
            ospf.build_instance(stage=True, **proposed_ospf)
            if lsa_generation_max:
                ospf.build_lsa(stage=True, **proposed_lsa)
            else:
                if bandwidth:
                    ospf.build_lsa(stage=True, **proposed_lsa)
        if proposed:
            if routerid:
                proposed_router = dict(ospfname=ospfname, routerid=routerid)
                ospf.build_instance(stage=True, **proposed_router)
                if area:
                    proposed_area = dict(ospfname=ospfname, area=area)
                    ospf.build_area(stage=True, **proposed_area)
                    if areatype:
                        proposed_area = dict(ospfname=ospfname, area=area, areatype=areatype)
                        ospf.build_area(stage=True, **proposed_area)
                    if networkaddr:
                        proposed_networks = dict(area=area, networkaddr=networkaddr,
                                                 wildcardmask=wildcardmask)
                        ospf.build_networks(stage=True, **proposed_networks)
            else:
                if area:
                    proposed_area = dict(ospfname=ospfname, area=area)
                    ospf.build_area(stage=True, **proposed_area)
                    if areatype:
                        proposed_area = dict(ospfname=ospfname, area=area, areatype=areatype)
                        ospf.build_area(stage=True, **proposed_area)
                    if networkaddr:
                        proposed_networks = dict(area=area, networkaddr=networkaddr,
                                                 wildcardmask=wildcardmask)
                        ospf.build_networks(stage=True, **proposed_networks)
        if import_route:
            proposed_import = dict(import_route=import_route)
            ospf.build_import(stage=True, **proposed_import)

    elif state == 'default':
        if ospfname:
            delta = dict(ospfname=ospfname)
            ospf.default(stage=True, **delta)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = ospf.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
