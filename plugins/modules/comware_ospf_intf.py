#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_ospf_intf
short_description: Manage ospf in interface
description:
    - Manage ospf in interface
version_added: 1.0.0
author: hanyangyang (@hanyangyang)
notes:
    - The module is used to config interface ospf setting , before using the module , please
      ensure the interface exists and is able to make ospf setting .
    - Interface ospf auth mode can config as simple or md5 , however these two mode can not be
      set at the same time.
    - Some of the setting must be set together e.g. ospfname must together with area.
    - state default or absent will delete all the ospf settings ,
options:
    name:
        description:
            - full name of interface
        required: true
        type: str
    ospfname:
        description:
            - Instance name.(1~65535)
        required: false
        type: str
    ospfcost:
        description:
            - Configure the overhead required for the interface to run OSPF
        required: false
        type: str
    area:
        description:
            - Specify the OSPF area
        required: false
        type: str
    simplepwdtype:
        description:
            - Specify the password type of ospf auth_mode simple
        required: false
        choices: ['cipher', 'plain']
        type: str
    simplepwd:
        description:
            - Specify the password  of ospf auth_mode simple
        required: false
        type: str
    keyid:
        description:
            - Specify the md5 or hwac-md5 key of ospf auth_mode
        required: false
        type: str
    md5type:
        description:
            - Specify the ospf auth_mode md5 type
        required: false
        choices: ['md5', 'hwac-md5']
        type: str
    md5pwdtype:
        description:
            - Specify the password type of ospf auth_mode md5
        required: false
        choices: ['cipher', 'plain']
        type: str
    md5pwd:
        description:
            - Specify the password of ospf auth_mode md5
        required: false
        type: str
    network_type:
        description:
            - Specify OSPF network type
        required: false
        choices: ['broadcast', 'nbma','p2p','p2mp']
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent','default']
        type: str
"""
EXAMPLES = """

      - name: Basic Ethernet config ensure interface name exists in device and the interface support ospf setting.
        h3c_open.comware.comware_ospf_intf:
          name: HundredGigE1/0/27
          ospfname: 1
          area: 0
          ospfcost: 10
          network_type: p2p
          keyid: 11
          md5type: md5
          md5pwdtype: plain
          md5pwd: 1
        register: results

      - name: delete config
        h3c_open.comware.comware_ospf_intf:
          name: HundredGigE1/0/27
          state: default
        register: results

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (get_device)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.ospf_intf import Ospf
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            ospfname=dict(required=False, type='str'),
            ospfcost=dict(required=False, type='str'),
            area=dict(required=False, type='str'),
            simplepwdtype=dict(choices=['cipher', 'plain'], type='str'),
            simplepwd=dict(type='str'),
            keyid=dict(no_log=True, type='str'),
            md5type=dict(choices=['md5', 'hwac-md5'], type='str'),
            md5pwdtype=dict(choices=['cipher', 'plain'], type='str'),
            md5pwd=dict(type='str'),
            network_type=dict(choices=['broadcast', 'nbma', 'p2p', 'p2mp'], type='str'),
            state=dict(choices=['present', 'absent', 'default'],
                       default='present',
                       type='str'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)

    state = module.params['state']
    name = module.params['name']
    ospfname = module.params['ospfname']
    ospfcost = module.params['ospfcost']
    area = module.params['area']
    simplepwdtype = module.params['simplepwdtype']
    simplepwd = module.params['simplepwd']
    keyid = module.params['keyid']
    md5type = module.params['md5type']
    md5pwdtype = module.params['md5pwdtype']
    md5pwd = module.params['md5pwd']
    network_type = module.params['network_type']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if simplepwdtype and md5type:
        safe_fail(module, msg='only one authentication-mode is effective')

    if area or ospfname:
        if module.params.get('area') and module.params.get('ospfname'):
            pass
        else:
            safe_fail(module, msg='param area must be setting together with ospfname')

    if simplepwd or simplepwdtype:
        if module.params.get('simplepwd') and module.params.get('simplepwdtype'):
            pass
        else:
            safe_fail(module, msg='param simplepwd must be setting together with simplepwdtype')

    if md5pwd or keyid or md5type or md5pwdtype:
        if module.params.get('md5pwd') and module.params.get('keyid') and \
                module.params.get('md5type') and module.params.get('md5pwdtype'):
            pass
        else:
            safe_fail(module,
                      msg='all the paramaters md5pwd keyid md5type md5pwdtype are needed when setting md5 auth mode')

    ospf_interface = None
    ospf = None
    try:
        ospf = Ospf(device, name)
        ospf_interface = Interface(device, name)
    except PYCW7Error as exe:
        safe_fail(module, descr='there is problem in setting ospf config',
                  msg=str(exe))

    if not ospf_interface.iface_exists:
        safe_fail(module, msg='interface does not exist.')
    is_eth, is_rtd = ospf_interface._is_ethernet_is_routed()
    if not is_rtd:
        safe_fail(module, msg='Interface is not l3 interface. please use interface module set first.')

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
    proposed_area = dict(ospfname=ospfname, area=area)
    proposed_cost = dict(ospfcost=ospfcost)
    proposed_nets = dict(network_type=network_type)
    proposed_spwd = dict(simplepwdtype=simplepwdtype,
                         simplepwd=simplepwd)
    proposed_md5 = dict(keyid=keyid, md5type=md5type,
                        md5pwdtype=md5pwdtype, md5pwd=md5pwd)

    if state == 'present':
        ospf.build_area(stage=True, **proposed_area)
        if ospfcost:
            ospf.build(stage=True, **proposed_cost)
            if network_type:
                ospf.build(stage=True, **proposed_nets)
                if simplepwd:
                    ospf.build_auth_simple(stage=True, state='present', **proposed_spwd)
                elif md5pwd:
                    ospf.build_auth_md5(stage=True, state='present', **proposed_md5)
            else:
                if simplepwd:
                    ospf.build_auth_simple(stage=True, state='present', **proposed_spwd)
                elif md5pwd:
                    ospf.build_auth_md5(stage=True, state='present', **proposed_md5)
        else:
            if network_type:
                ospf.build(stage=True, **proposed_nets)
                if simplepwd:
                    ospf.build_auth_simple(stage=True, state='present', **proposed_spwd)
                elif md5pwd:
                    ospf.build_auth_md5(stage=True, state='present', **proposed_md5)
            else:
                if simplepwd:
                    ospf.build_auth_simple(stage=True, state='present', **proposed_spwd)
                elif md5pwd:
                    ospf.build_auth_md5(stage=True, state='present', **proposed_md5)

    elif state == 'absent' or state == 'default':
        if existing:
            ospf.default_ospf(stage=True)

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
