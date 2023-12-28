#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_bgp_group
short_description: create and config bgp group
description:
    - create and config bgp group
version_added: 1.0.0
author: hanyangyang (@hanyangyang)
notes:
    - Connect interface must be exist in the device if you want use it.
    - If you want join a peer in a group , the group must be already exist.
    - Bgp with and without instance are in different view , carefully config it.
options:
    bgp_as:
        description:
            - Autonomous system number <1-4294967295>
        required: True
        type: str
    instance:
        description:
            - Specify a BGP instance by its name
        required: false
        type: str
    group:
        description:
            - Create a peer group
        required: false
        type: str
    group_type:
        description:
            - Group type , include external and internal
        required: false
        choices: ['external','internal']
        type: str
    peer:
        description:
            - Specify BGP peers , a group or peer ID
        required: false
        type: str
    peer_connect_intf:
        description:
            - Set interface name to be used as session's output interface
        required: false
        type: str
    peer_in_group:
        description:
            - Specify a peer-group
        required: false
        type: str
    address_family:
        description:
            - Specify an address family , only l2vpn can be config here
        required: false
        choices: ['l2vpn']
        type: str
    evpn:
        description:
            - Specify the EVPN address family
        required: false
        default: 'false'
        choices: ['true', 'false']
        type: str
    policy_vpn_target:
        description:
            - Filter VPN routes with VPN-Target attribute
        required: false
        default: enable
        choices: ['enable', 'disable']
        type: str
    reflect_client:
        description:
            - Configure the peers as route reflectors
        required: false
        default: 'false'
        choices: ['true', 'false']
        type: str
    peer_group_state:
        description:
            - Enable or disable the specified peers
        required: false
        choices: ['true', 'false']
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present',  'default']
        type: str
"""
EXAMPLES = """
- name: config bgp and create group
  h3c_open.comware.comware_bgp_group:
    bgp_as: 200
    group: evpn
    group_type: internal

- name: Config peer connet interface
  h3c_open.comware.comware_bgp_group:
    bgp_as: 200
    peer: evpn
    peer_connect_intf: LoopBack0

- name: Join peer in the group
  h3c_open.comware.comware_bgp_group:
    bgp_as: 200
    peer: 1.1.1.1
    peer_in_group: evpn

- name: Join peer in the group
  h3c_open.comware.comware_bgp_group:
    bgp_as: 200
    peer: 3.3.3.3
    peer_in_group: evpn

- name: Create address-family view and config it
  h3c_open.comware.comware_bgp_group:
    bgp_as: 200
    address_family: l2vpn
    evpn: true
    policy_vpn_target: disable
    peer: evpn
    reflect_client: true
    peer_group_state: true

- name: Remove bgp
  h3c_open.comware.comware_bgp_group:
    bgp_as: 200
    state: default
"""

import re

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.bgp_group import Bgp
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            bgp_as=dict(required=True, type='str'),
            instance=dict(required=False, type='str'),
            group=dict(type='str'),
            group_type=dict(choices=['external', 'internal'], type='str'),
            peer=dict(type='str'),
            peer_connect_intf=dict(type='str'),
            peer_in_group=dict(type='str'),
            address_family=dict(choices=['l2vpn'], type='str'),
            evpn=dict(choices=['true', 'false'],
                      default='false',
                      type='str'),
            policy_vpn_target=dict(choices=['enable', 'disable'],
                                   default='enable',
                                   type='str'),
            reflect_client=dict(choices=['true', 'false'],
                                default='false',
                                type='str'),
            peer_group_state=dict(choices=['true', 'false'], type='str'),
            state=dict(choices=['present', 'default'],
                       default='present',
                       type='str'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    bgp_as = module.params['bgp_as']
    instance = module.params['instance']
    peer = module.params['peer']
    peer_connect_intf = module.params['peer_connect_intf']
    peer_in_group = module.params['peer_in_group']

    interface = None
    bgp_config = None
    existing = None
    if peer_connect_intf:
        try:
            interface = Interface(device, peer_connect_intf)
        except PYCW7Error:
            safe_fail(module, msg='There was problem recognizing that interface.')

        if not interface.iface_exists:
            safe_fail(module, msg='Interface does not exist , please use comware_interface module create it')

    try:
        bgp_config = Bgp(device, bgp_as, instance)
    except PYCW7Error:
        safe_fail(module, msg='there is problem in creating bgp instance')

    try:
        existing = bgp_config.get_config()
    except PYCW7Error:
        safe_fail(module, msg='Error getting existing config.')

    if peer_in_group:
        existing_group = bgp_config.get_group_info(peer_in_group)
        if not existing_group:
            safe_fail(module, msg='The specified peer group {0} doesn\'t exist '.format(peer_in_group))

    if peer:
        res = re.search(r'\.', peer)
        if not res:
            existing_group = bgp_config.get_group_info(peer)
            if not existing_group:
                safe_fail(module, msg='The specified peer group {0} doesn\'t exist '.format(peer_in_group))

    if state == 'present':
        delta = proposed
        if delta:
            bgp_config.build_bgp_group(stage=True, **delta)

    elif state == 'default':
        default_bgp = dict(bgp_as=bgp_as, instance=instance)
        bgp_config.remove_bgp(stage=True, **default_bgp)

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
                end_state = bgp_config.get_config()
            except PYCW7Error as e:
                safe_fail(module, msg=str(e),
                          descr='Error on device execution.')
            changed = True

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['state'] = state
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = end_state

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
