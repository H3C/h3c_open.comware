#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_isis_global
short_description: Manage isis for Comware 7 devices
description:
    - Manage isis for Comware 7 devices
author: gongqianyu(@gongqianyu)
version_added: 1.0.0
options:
    isisID:
        description:
            - create isis process
        required: true
        type: str
    level:
        description:
            - Configure the level of the router,the default value is Level-1-2.
        required: false
        default: 'level-1-2'
        choices: ['level-1', 'level-1-2', 'level-2']
        type: str
    cost_style:
        description:
            - Configure the type of IS-IS overhead value, that is,
              the type of destination path overhead value in the message received and sent by IS-IS.
        required: false
        choices: ['narrow', 'wide', 'wide-compatible', 'compatible', 'narrow-compatible']
        type: str
    spf_limit:
        description:
            - Indicates that it is allowed to receive a message with a destination path overhead value
              greater than 1023. If this parameter is not specified, a message with an overhead value greater than
              1023 will be discarded. This parameter is optional only when compatible or narrow compatible is specified.
        required: false
        choices: ['true', 'false']
        type: str
    network:
        description:
            - Network entity name of the configuration IS-IS process(X...X.XXXX....XXXX.00)
        required: false
        type: str
    add_family:
        description:
            - Create IS-IS IPv4 or IPV6 address family and enter IS-IS IPv4 address family view
        required: false
        choices: ['ipv4', 'ipv6']
        type: str
    preference:
        description:
            - Configure routing priority of IS-IS protocol(1~225),before config it,you need to
              config add_family first.
        required: false
        type: str
    state:
        description:
            - Desired state of the vlan
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
"""
EXAMPLES = """

      - name: create isis 4 and related params.
        h3c_open.comware.comware_isis_global:
          isisID: 4
          level: level-2
          cost_style: narrow-compatible
          spf_limit: true
          network: 10.0001.1010.1020.1030.00
          add_family: ipv4
          preference: 25
          state: present
        register: results

      - name: delete isis 4
        h3c_open.comware.comware_isis_global:
          isisID: 4
          level: level-2
          cost_style: narrow-compatible
          spf_limit: true
          network: 10.0001.1010.1020.1030.00
          add_family: ipv4
          preference: 25
          state: absent
        register: results

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.isis_global import Isis
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.isis_global import ISis
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            isisID=dict(required=True, type='str'),
            level=dict(required=False, choices=['level-1', 'level-1-2', 'level-2'], default='level-1-2', type='str'),
            cost_style=dict(required=False,
                            choices=['narrow', 'wide', 'wide-compatible', 'compatible', 'narrow-compatible'],
                            type='str'),
            spf_limit=dict(required=False, choices=['true', 'false'], type='str'),
            network=dict(required=False, type='str'),
            add_family=dict(required=False, choices=['ipv4', 'ipv6'], type='str'),
            preference=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    isisID = module.params['isisID']
    cost_style = module.params['cost_style']
    spf_limit = module.params['spf_limit']
    network = module.params['network']
    add_family = module.params['add_family']
    level = module.params['level']
    preference = module.params['preference']
    state = module.params['state']

    changed = False

    args = dict(isisID=isisID, network=network, level=level, cost_style=cost_style, spf_limit=spf_limit,
                preference=preference, add_family=add_family)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    isis = None
    iSis = None
    try:

        isis = Isis(device, isisID)
        iSis = ISis(device, isisID, level, cost_style, spf_limit, preference, add_family, network)
    #     isis.param_check(**proposed)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    existing = None
    try:
        existing = isis.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='error getting isis config')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            if (module.params['network'] or module.params['cost_style'] or module.params['preference'] or
                    module.params['spf_limit'] or module.params['add_family'] or module.params['level']):
                iSis.build(stage=True)
            else:
                isis.build(stage=True, **delta)
    elif state == 'absent':
        if existing:
            isis.remove(stage=True)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            device.close()
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = isis.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='error during execution')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
