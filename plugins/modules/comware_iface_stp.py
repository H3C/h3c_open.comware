#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_iface_stp
short_description: Manage stp config in interface
description:
    - Manage stp config in interface
version_added: 1.0.0
author: hanyangyang (@hanyangyang)
notes:
    - stp interface configs must be setting in l2 ethernet mode .
    - loop protect is conflict with edgeport and root protect , while loop protect
      exists , edgeport and root protect can not be set , vice versa.

options:
    name:
        description:
            - Full name of the interface
        required: True
        type: str
    edgedport:
        description:
            - Specify edge port
        required: false
        choices: ['true', 'false']
        type: str
    loop:
        description:
            - Specify loop protection
        required: false
        choices: ['true', 'false']
        type: str
    root:
        description:
            - Specify root protection
        required: false
        choices: ['true', 'false']
        type: str
    tc_restriction:
        description:
            - Restrict propagation of TC message
        required: false
        choices: ['true', 'false']
        type: str
    transmit_limit:
        description:
            - Specify transmission limit count
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent', 'default']
        type: str
"""
EXAMPLES = """
- name: Basic interface stp config
  h3c_open.comware.comware_iface_stp:
    name: Twenty-FiveGigE1/0/22
    tc_restriction: true
    transmit_limit: 200

- name: Delete interface stp config
  h3c_open.comware.comware_iface_stp:
    name: Twenty-FiveGigE1/0/22
    state: default

- name: Interface stp full configuration
  h3c_open.comware.comware_iface_stp:
    name: Ten-GigabitEthernet2/0/25
    edgedport: true
    root: true
    tc_restriction: true
    transmit_limit: 200
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.iface_stp import Stp


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            edgedport=dict(required=False, choices=['true', 'false', ]),
            loop=dict(required=False, choices=['true', 'false', ]),
            root=dict(required=False, choices=['true', 'false', ]),
            tc_restriction=dict(required=False, choices=['true', 'false', ]),
            transmit_limit=dict(type='str'),
            state=dict(choices=['present', 'absent', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    name = module.params['name']
    changed = False

    if module.params['edgedport'] or module.params['root']:
        if module.params['loop']:
            module.fail_json(msg='loop protect can not be set \
            while edgeport or root protect exist')
    if module.params['loop']:
        if module.params['edgedport'] or module.params['root']:
            module.fail_json(msg='edgeport or root protect can not be set \
                        while loop protect exist')

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)
    stp = None
    try:
        stp = Stp(device, name)
    except PYCW7Error as e:
        module.fail_json(descr='there is problem in setting stp config',
                         msg=str(e))
    existing = {}
    try:
        existing = stp.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            stp.build(stage=True, **delta)

    elif state == 'default' or state == 'absent':
        defaults = stp.get_default_config()
        delta = dict(set(existing.items()).difference(
            defaults.items()))
        if delta:
            stp.default(stage=True)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = stp.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='Error on device execution.')
            changed = True

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['state'] = state
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == "__main__":
    main()
