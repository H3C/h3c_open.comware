#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_vxlan_tunnel
short_description: Manage VXLAN tunnels on Comware 7 devices
description:
    - Manage VXLAN tunnels on Comware 7 devices
version_added: 1.0.0
author: h3c(@h3c_open)
notes:
    - state=absent removes the tunnel interface if it exists
    - state=absent can also remove non-vxlan tunnel interfaces
options:
    tunnel:
        description:
            - Tunnel interface identifier
        required: true
        type: str
    global_src:
        description:
            - Global source address for VXLAN tunnels
        required: false
        type: str
    src:
        description:
            - Source address or interface for the tunnel
        required: false
        type: str
    dest:
        description:
            - Destination address for the tunnel
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent']
        type: str

"""
EXAMPLES = """

# ensure tunnel interface 20 exists for vxlan and configures a global source address (although it's not used here)
- comware_vxlan_tunnel:
    tunnel: 20
    global_src: 10.10.10.10
    src: 10.1.1.1
    dest: 10.1.1.2

# ensure tunnel interface 21
- comware_vxlan_tunnel:
    tunnel: 21
    src: 10.1.1.1
    dest: 10.1.1.2


# ensure tunnel interface 21 does not exist (does not have to be a vxlan tunnel)
- comware_vxlan_tunnel:
    tunnel: 21
    state: absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.l2vpn import L2VPN
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vxlan import Tunnel


def main():
    module = AnsibleModule(
        argument_spec=dict(
            tunnel=dict(required=True, type='str'),
            src=dict(required=False, type='str'),
            dest=dict(required=False, type='str'),
            global_src=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    tunnel = module.params['tunnel']
    src = module.params['src']
    dest = module.params['dest']
    global_src = module.params['global_src']

    state = module.params['state']

    changed = False
    args = dict(src=src, dest=dest)
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    is_l2vpn_enabled = 'disabled'
    try:
        l2vpn = L2VPN(device)
        is_l2vpn_enabled = l2vpn.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='L2VPN check failed')

    if is_l2vpn_enabled == 'disabled':
        module.fail_json(msg='l2vpn needs to be enabled.')
    existing = {}
    tun = None
    try:
        tun = Tunnel(device, tunnel)
        existing = tun.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='could not get tunnel config')

    if state == 'present':
        if existing.get('mode') and existing.get('mode') != 'vxlan':
            module.fail_json(msg='tunnel interface exists but is not a '
                                 + 'vxlan \ntunnel interface. remove and re-add.')

    delta = dict(set(proposed.items()).difference(
        existing.items()))
    existing_gsrc = {}
    try:
        existing_gsrc = tun.get_global_source()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='could not get existing global src')

    if global_src:
        if existing_gsrc != global_src:
            delta['global_src'] = global_src
    if state == 'present':
        if delta or not existing:
            tun.build(stage=True, **delta)
    elif state == 'absent':
        if existing:
            tun.remove(stage=True)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            device.close()
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = tun.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')
            end_state['global_src'] = tun.get_global_source()
            changed = True

    proposed['global_src'] = global_src
    existing['global_src'] = existing_gsrc

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
