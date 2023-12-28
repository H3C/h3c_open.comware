#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_lldp_interface
short_description: Manage lldp enable on interfaces.The default state is enable.
description:
    - Manage lldp enable on interfaces.The default state is enable.
version_added: 1.0.0
author: gongqianyu(@gongqianyu)
notes:
    - Before config interface lldp enable, the global lldp must be enable.
options:
    name:
        description:
            - Full name of the interface
        required: true
        type: str
    interface_enable:
        description:
            - Layer 2 mode of the interface
        required: true
        choices: ['enabled', 'disabled']
        type: str
    state:
        description:
            - Desired state of the interface lldp state.
        required: false
        default: present
        choices: ['present', 'default']
        type: str
"""
EXAMPLES = """

  - name: Manage lldp interface enable
    h3c_open.comware.comware_lldp_interface:
      name: HundredGigE1/0/28
      interface_enable: enabled
    register: results

  - name: Manage lldp global disable
    h3c_open.comware.comware_lldp_interface:
      name: HundredGigE1/0/28
      interface_enable: disabled
    register: results

  - name: Manage lldp global default
    h3c_open.comware.comware_lldp_interface:
      name: HundredGigE1/0/28
      interface_enable: enabled
      state: default
    register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.lldp_interface import Lldp


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            interface_enable=dict(required=True,
                                  choices=['enabled', 'disabled'],
                                  type='str'),
            state=dict(choices=['present', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)

    name = module.params['name']
    state = module.params['state']
    changed = False

    lldp = None
    existing = []
    try:
        lldp = Lldp(device, name)
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error initialzing Switchport object.')

    # Make sure interface exists and is ethernet
    if not lldp.interface.iface_exists:
        module.fail_json(msg='{0} doesn\'t exist on the device.'.format(name))

    try:
        existing = lldp.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting lldp config.')

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))

        if delta:
            delta['interface_enable'] = proposed.get('interface_enable')
            lldp.build(stage=True, **delta)
    elif state == 'default':
        defaults = lldp.get_default()
        delta = dict(set(existing.items()).difference(
            defaults.items()))
        if delta:
            lldp.default(stage=True)

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
                end_state = lldp.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='Error during command execution.')
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
