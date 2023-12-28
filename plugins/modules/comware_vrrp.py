#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_vrrp
short_description: Manage VRRP configurations on a Comware v7 device
description:
    - Manage VRRP configurations on a Comware v7 device
author: hanyangyang (@hanyangyang)
version_added: 1.0.0
notes:
    - When state is set to absent, the vrrp group for a specific
      interface will be removed (if it exists)
    - When state is set to shutdown, the vrrp group for a specific
      interface will be shutdown. undoshutdown reverses this operation
    - When sending a text password, the module is not idempotent
      because a hash is calculated on the switch. sending a cipher
      that matches the one configured is idempotent.
options:
    vrid:
        description:
            - VRRP group ID number
        required: true
        type: str
    interface:
        description:
            - Full name of the Layer 3 interface
        required: true
        type: str
    vip:
        description:
            - Virtual IP to assign within the group
        required: false
        type: str
    priority:
        description:
            - VRRP priority for the device
        required: false
        type: str
    preempt:
        description:
            - Determine preempt mode for the device
        required: false
        choices: ['yes', 'no']
        type: str
    auth_mode:
        description:
            - authentication mode for vrrp
        required: false
        choices: ['simple', 'md5']
        type: str
    key_type:
        description:
            - Type of key, i.e. cipher or clear text
        required: false
        choices: ['cipher', 'plain']
        type: str
    key:
        description:
            - cipher or clear text string
        required: false
        type: str
    delay:
        description:
            - Configure preemption delay time
        required: false
        type: str
    track:
        description:
            - Configure the track entry specified for monitoring.
        required: false
        type: str
    switch:
        description:
            - when the status of the monitored track item changes to negative,
              if the router is in backup status in the backup group, it will immediately switch to master router
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent', 'shutdown', 'undoshutdown']
        type: str

"""
EXAMPLES = """

  - name: Ensure vrid 100 on vlan 100 does not existing before testing
    h3c_open.comware.comware_vrrp:
      vrid: 100
      interface: vlan100
      state: absent

  - name: Ensure vrid and vrip are configured
    h3c_open.comware.comware_vrrp:
      vrid: 100
      vip: 100.100.100.1
      interface: vlan100
    register: data

  - assert:
      that:
        - data.end_state.vip == '100.100.100.1'
        - data.end_state.vrid == '100'
        - data.end_state.preempt == 'yes'

  - name: Same config - idempotency check
    h3c_open.comware.comware_vrrp:
      vrid: 100
      vip: 100.100.100.1
      interface: vlan100
    register: data

  - assert:
      that:
        - data.changed == false

  - name: Ensure preempt is no
    h3c_open.comware.comware_vrrp:
      vrid: 100
      vip: 100.100.100.1
      interface: vlan100
      preempt: false
    register: data

  - assert:
      that:
        - data.end_state.preempt == 'no'
        - data.end_state.vrid == '100'
        - data.end_state.vip == '100.100.100.1'
        - data.end_state.vrid == '100'

  - name: Ensure vrid 100 is down
    h3c_open.comware.comware_vrrp:
      vrid: 100
      interface: vlan100
      state: shutdown
    register: data

  - assert:
      that:
        - data.end_state.admin == 'Down'
        - data.end_state.preempt == 'no'
        - data.end_state.vrid == '100'
        - data.end_state.vip == '100.100.100.1'
        - data.end_state.vrid == '100'
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vrrp import VRRP


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vrid=dict(required=True, type='str'),
            interface=dict(required=True, type='str'),
            vip=dict(required=False, type='str'),
            priority=dict(required=False, type='str'),
            auth_mode=dict(required=False, choices=['simple', 'md5'], type='str'),
            key_type=dict(required=False, choices=['cipher', 'plain'], type='str'),
            key=dict(required=False, no_log=True, type='str'),
            preempt=dict(required=False, choices=['yes', 'no'], type='str'),
            delay=dict(required=False, type='str'),
            track=dict(required=False, type='str'),
            switch=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent', 'shutdown',
                                'undoshutdown'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    vrid = module.params['vrid']
    interface = module.params['interface'].lower()
    vip = module.params['vip']
    priority = module.params['priority']
    preempt = module.params['preempt']
    auth_mode = module.params['auth_mode']
    key_type = module.params['key_type']
    key = module.params['key']
    delay = module.params['delay']
    track = module.params['track']
    switch = module.params['switch']

    if auth_mode:
        if not key_type or not key:
            module.fail_json(msg='params key_type and key are required')
    if key_type or key:
        if not auth_mode:
            module.fail_json(msg='auth_mode is required when setting auth')
    if delay:
        if int(delay) < 0 or int(delay) > 180000:
            module.fail_json(msg='error delay time give')
    if track:
        if int(track) < 1 or int(track) > 1024:
            module.fail_json(msg='error track entry NUM give')
    if track:
        if not switch:
            module.fail_json(msg='params switch is requied')
    if switch:
        if not track:
            module.fail_json(msg='track is required when setting switch')

    state = module.params['state']

    changed = False

    args = dict(vrid=vrid, priority=priority, preempt=preempt,
                vip=vip, interface=interface, auth_mode=auth_mode,
                key_type=key_type, key=key, delay=delay, track=track,
                switch=switch)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    vrrp = None
    vrrp_interface = None
    existing = []
    try:
        vrrp = VRRP(device, interface, vrid)
        vrrp_interface = Interface(device, interface)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    if not vrrp_interface.iface_exists:
        module.fail_json(msg='interface does not exist.')
    is_eth, is_rtd = vrrp_interface._is_ethernet_is_routed()
    if not is_rtd:
        module.fail_json(msg='interface needs to be a layer 3 interface')

    try:
        existing = vrrp.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='could not get existing config')
    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta or auth_mode or \
                existing.get('admin') == 'down':
            delta['vrid'] = vrid
            if delta.get('key'):
                delta['auth_mode'] = auth_mode
                delta['key_type'] = key_type
            vrrp.build(stage=True, state=state, **delta)
    elif state == 'absent':
        if existing:
            vrrp.remove(stage=True)
    elif state == 'shutdown':
        if existing.get('admin') == 'Up':
            vrrp.shutdown(stage=True)
    elif state == 'undoshutdown':
        if existing.get('admin') == 'Down':
            vrrp.undoshutdown(stage=True)

    commands = None
    end_state = existing
    response = None

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            device.close()
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                response = device.execute_staged()
                end_state = vrrp.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')
            changed = True

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['state'] = state
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = end_state
    results['response'] = response

    module.exit_json(**results)


if __name__ == "__main__":
    main()
