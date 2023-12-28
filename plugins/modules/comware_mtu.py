#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2023 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_mtu
short_description: Manage mtu and jumboframe of the interface
description:
    - Manage mtu and jumboframe of the interface
version_added: 1.0.0
author: hanyangyang (@hanyangyang)
notes:
    - mtu can be set in interface type of ['GigabitEthernet','Ten-GigabitEthernet','FortyGigE',
      'Vlan-interface','Route-Aggregation','TwentyGigE','Twenty-FiveGigE','HundredGigE'] and
      some of these must be set as route mode.
    - jumboframe can be set in interface type of ['GigabitEthernet','Ten-GigabitEthernet',
      'FortyGigE','Bridge-Aggregation','Route-Aggregation','TwentyGigE','Twenty-FiveGigE','HundredGigE']
options:
    name:
        description:
            - Full name of the interface
        required: true
        type: str
    mtu:
        description:
            - Specify Maximum Transmission Unit(MTU) of the interface
        required: false
        type: str
    jumboframe:
        description:
            - Specify Maximum jumbo frame size allowed of the interface
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
  - name: Basic Ethernet config
    h3c_open.comware.comware_mtu:
      name: HundredGigE1/0/32
      jumboframe: 1537
      mtu: 1600
"""


from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.mtu import Mtu


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            mtu=dict(type='str'),
            jumboframe=dict(type='str'),
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
    mtu = module.params['mtu']
    jumboframe = module.params['jumboframe']

    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    try:
        mtu = Mtu(device, name)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem recognizing that interface.',
                         msg=str(e))

    try:
        mtu.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(e))
    args = {}
    if module.params.get('jumboframe'):
        args = dict(jumboframe=jumboframe)

    existing = {}
    try:
        existing = mtu.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if module.params.get('jumboframe'):
            mtu.build_jumbo(stage=True, **args)
            del delta['jumboframe']
        if delta or not existing:
            if not mtu.iface_exists:
                try:
                    mtu.create_logical()
                    mtu.update()
                    changed = True
                    existing = mtu.get_config()
                except PYCW7Error as e:
                    module.fail_json(msg='Exception message ' + str(e),
                                     descr='There was a problem creating'
                                           + ' the logical interface.')
                delta = dict(set(proposed.items()).difference(
                    existing.items()))

            if delta:
                mtu.build(stage=True, **delta)
    elif state == 'default':
        defaults = mtu.get_default_config()
        delta = dict(set(existing.items()).difference(
            defaults.items()))
        jumbo_config = mtu.get_jumbo_config()
        if jumbo_config:
            jumbo_lst = []
            for k, v in jumbo_config.items():
                jumbo_lst.append(v)
            # jumboframe default 9416
            if int(jumbo_lst[0]) != 9416:
                mtu.remove_jumbo(stage=True, **jumbo_config)
        if delta:
            mtu.default(stage=True)

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
                end_state = mtu.get_config()
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
