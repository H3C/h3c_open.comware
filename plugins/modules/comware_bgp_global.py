#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_bgp_global
short_description: config bgp configs in the bgp instance view such as routerid
description:
    - config bgp configs in the bgp instance view such as routerid
version_added: 1.0.0
author: hanyangyang (@hanyangyang)
notes:
    - all the configs except bgp_as and bgp_instance are set in bgp instance view.
    - timer keepalive and time hold must be set together .
    - timer hold must be greater than 3 times timer keepalive.
    - peer relations are need peer ip first.
    - state default and absent are the same , if you want delete the setting configs , the comware
      will undo the bgp_as and instance .
options:
    bgp_as:
        description:
            - Autonomous system number <1-4294967295>
        required: True
        type: str
    bgp_instance:
        description:
            - Specify a BGP instance by its name
        required: false
        type: str
    router_id:
        description:
            - Router ID in IP address format
        required: false
        type: str
    advertise_rib_active:
        description:
            - Advertise the best route in IP routing table
        required: false
        default: 'false'
        choices: ['true', 'false']
        type: str
    timer_connect_retry:
        description:
            - Configure the session retry timer for all BGP peers
        required: false
        type: str
    timer_keepalive:
        description:
            - Keepalive timer ,Value of keepalive timer in seconds
        required: false
        type: str
    timer_hold:
        description:
            - Hold timer , Value of hold timer in seconds
        required: false
        type: str
    compare_as_med:
        description:
            - Compare the MEDs of routes from different ASs
        required: false
        default: 'false'
        choices: ['true', 'false']
        type: str
    peer_ip:
        description:
            - Specify BGP peers IPv4 address
        required: false
        type: str
    peer_as_num:
        description:
            - Specify BGP peers AS number
        required: false
        type: str
    peer_connect_intf:
        description:
            - Peer connect interface
        required: false
        type: str
    address_family:
        description:
            - Specify an address family
        required: false
        choices: ['l2vpn']
        type: str
    peer_ignore:
        description:
            - Disable session establishment with the peers
        required: false
        default: 'false'
        choices: ['true', 'false']
        type: str
    evpn:
        description:
            - Disable specify the EVPN address family
        required: false
        default: 'false'
        choices: ['true', 'false']
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

      - name: bgp global views configs
        h3c_open.comware.comware_bgp_global:
          bgp_as: 10
          bgp_instance: test
          router_id: 192.168.1.185
          advertise_rib_active: true
          timer_connect_retry: 100
          timer_keepalive: 100
          timer_hold: 301
          compare_as_med: true
          peer_ip: 1.1.1.3
          peer_as_num: 10
          peer_ignore: true
        register: results

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.bgp_global import Bgp
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            bgp_as=dict(required=True, type='str'),
            bgp_instance=dict(required=False, type='str'),
            router_id=dict(type='str'),
            advertise_rib_active=dict(choices=['true', 'false'],
                                      default='false',
                                      type='str'),
            timer_connect_retry=dict(type='str'),
            timer_keepalive=dict(type='str'),
            timer_hold=dict(type='str'),
            compare_as_med=dict(choices=['true', 'false'],
                                default='false',
                                type='str'),
            peer_ip=dict(type='str'),
            peer_as_num=dict(type='str'),
            peer_ignore=dict(choices=['true', 'false'],
                             default='false',
                             type='str'),
            peer_connect_intf=dict(type='str'),
            address_family=dict(choices=['l2vpn'],
                                type='str'),
            evpn=dict(choices=['true', 'false'],
                      default='false',
                      type='str'),
            state=dict(choices=['present', 'absent', 'default'],
                       default='present',
                       type='str'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    bgp_as = module.params['bgp_as']
    bgp_instance = module.params['bgp_instance']
    timer_keepalive = module.params['timer_keepalive']
    timer_hold = module.params['timer_hold']
    peer_as_num = module.params['peer_as_num']
    peer_ignore = module.params['peer_ignore']
    peer_connect_intf = module.params['peer_connect_intf']
    evpn = module.params['evpn']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if timer_keepalive:
        if not module.params.get('timer_hold'):
            safe_fail(module, msg='timer keepalive and hold config at the same time')
    if timer_hold:
        if not module.params.get('timer_keepalive'):
            safe_fail(module, msg='timer keepalive and hold config at the same time')
    if timer_keepalive:
        if int(timer_keepalive) < 0 or int(timer_keepalive) > 21845:
            safe_fail(module, msg='keepalive time not in the range')
    if timer_hold:
        if int(timer_hold) < 0 or int(timer_hold) > 65535:
            safe_fail(module, msg='hold time not in the range')
    if timer_keepalive and timer_hold:
        if int(timer_keepalive) * 3 > int(timer_hold):
            safe_fail(module, msg='hold time must be bigger than triple-keepalive time')

    if peer_as_num:
        if int(peer_as_num) < 0 or int(peer_as_num) > 4294967295:
            safe_fail(module, msg='peer_as_num is not in the range')
    if peer_as_num:
        if module.params.get('peer_ip') is None:
            safe_fail(module, msg='peer ip is required when')
    if peer_ignore:
        if module.params.get('peer_ip') is None:
            safe_fail(module, msg='peer ip is required when setting ignore')
    if peer_connect_intf:
        if module.params.get('peer_ip') is None:
            safe_fail(module, msg='peer ip is required when setting connect-interface')
    if evpn == 'true':
        if module.params.get('address_family') is None:
            safe_fail(module, msg='address_family is required when setting evpn')

    interface = None
    if peer_connect_intf:
        try:
            interface = Interface(device, peer_connect_intf)
        except PYCW7Error as exe:
            safe_fail(module, descr='There was problem recognizing that interface.', msg=str(exe))

        if not interface.iface_exists:
            safe_fail(module, msg='Interfce does not exist , please use comware_interface module create it')

    bgp = None
    try:
        bgp = Bgp(device, )
    except PYCW7Error as exe:
        safe_fail(module, descr='there is problem in creating bgp instance',
                  msg=str(exe))
    existing = None
    try:
        existing = bgp.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting existing config.')

    if state == 'present':
        delta = proposed
        if delta:
            bgp.build_bgp_global(stage=True, **delta)

    elif state == 'default' or state == 'absent':
        default_bgp = dict(bgp_as=bgp_as,
                           bgp_instance=bgp_instance)
        bgp.remove_bgp(stage=True, **default_bgp)

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
                end_state = bgp.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
