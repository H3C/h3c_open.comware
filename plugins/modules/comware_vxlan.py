#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_vxlan
short_description: Manage VXLAN to VSI mappings and Tunnel mappings to VXLAN
description:
    - Manage VXLAN to VSI mappings and Tunnel mappings to VXLAN
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - VXLAN tunnels should be created before using this module.
    - state=absent removes the vsi and associated vxlan mapping if they both
      exist.
    - Remember that is a 1 to 1 mapping between vxlan IDs and VSIs
options:
    vxlan:
        description:
            - VXLAN that will be mapped to the VSI
        required: true
        type: str
    vsi:
        description:
            - Name of the VSI
        required: true
        type: str
    descr:
        description:
            - description of the VSI
        required: false
        type: str
    tunnels:
        description:
            - Desired Tunnel interface ID or a list of IDs.
              Any tunnel not in the list will be removed if it exists
        required: false
        elements: str
        type: list
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
"""
EXAMPLES = """

# ensure VXLAN and VSI do not exist
- comware_vxlan:
    vxlan: 100
    vsi: VSI_VXLAN_100
    tunnels: [20]
    state: absent

# ensure VXLAN 100 exists and is mapped to VSI VSI_VXLAN_100 with only tunnel interface 20
- comware_vxlan:
    vxlan: 100
    vsi: VSI_VXLAN_100
    tunnels: [20]

# ensure 3 tunnels mapped to the vxlan
- comware_vxlan:
    vxlan: 100
    vsi: VSI_VXLAN_100
    tunnels: ['20', '21', '22']
"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.l2vpn import L2VPN
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vxlan import Tunnel
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vxlan import Vxlan


def normalize_to_list(data):
    if isinstance(data, str):
        return [data]
    elif isinstance(data, list):
        return data
    else:
        return []


def checks(existing, proposed, module):
    if existing.get('vsi') and proposed.get('vsi'):
        if proposed.get('vsi') != existing.get('vsi'):
            module.fail_json(msg='vxlan already assigned to another vsi.'
                                 + '\nremove it first.', vsi=existing.get('vsi'))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vxlan=dict(required=True, type='str'),
            vsi=dict(required=True, type='str'),
            tunnels=dict(required=False, type='list', elements='str'),
            descr=dict(required=False),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    vxlan = module.params['vxlan']
    vsi = module.params['vsi']
    descr = module.params['descr']
    tunnels = normalize_to_list(module.params['tunnels'])
    state = module.params['state']
    changed = False

    args = dict(vxlan=vxlan, vsi=vsi, descr=descr)
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
    vxlan_ins = None
    try:
        vxlan_ins = Vxlan(device, vxlan, vsi)
        existing = vxlan_ins.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='could not obtain existing')

    if state == 'present':
        checks(existing, proposed, module)

    if 'tunnels' in existing.keys():
        existing_tunnels = existing.pop('tunnels')
    else:
        existing_tunnels = []

    delta = dict(set(proposed.items()).difference(
        existing.items()))
    tunnels_to_add = list(set(tunnels).difference(existing_tunnels))
    tunnels_to_remove = list(set(existing_tunnels).difference(tunnels))
    if tunnels_to_add:
        delta['tunnels_to_add'] = tunnels_to_add
        for each in tunnels_to_add:
            tun = Tunnel(device, each)
            exists = tun.get_config()
            if not exists:
                module.fail_json(msg='tunnel needs to exist first'
                                     + ' before \nbefore adding it to a vxlan',
                                 tunnel=each)
    if tunnels_to_remove:
        delta['tunnels_to_remove'] = tunnels_to_remove

    if state == 'present':
        if not existing.get('vxlan'):
            vxlan_ins.create(stage=True)
        if delta:
            vxlan_ins.build(stage=True, **delta)
    elif state == 'absent':
        if existing:
            # existing is based off the VXLAN ID
            # if it's not mapped to any VSI, it's not considered
            # existing although the VSI may exist
            if existing.get('vsi') != vsi:
                module.fail_json(msg='vsi/vxlan mapping must exist'
                                     + ' on switch to remove it', current_vsi=existing.get('vsi'))
            else:
                vxlan_ins.remove_vsi(stage=True)

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
                end_state = vxlan_ins.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='failed during execution')
            changed = True

    if tunnels:
        proposed.update(tunnels=tunnels)
    if existing_tunnels:
        existing.update(tunnels=existing_tunnels)

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
