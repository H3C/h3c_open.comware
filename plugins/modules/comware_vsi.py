#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_vsi
short_description: Configure some command functions of vsi view
description:
    - Configure some command functions of vsi view
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - l2vpn needs to enabled before config vsi view.
    - If you want to use vsi gateway interface, it must be exist , you can use interface module to create it.
    - when giving vsi and state is absent , it will delete the given vsi config all.
options:
    vsi:
        description:
            - Name of the vsi_ins
        required: true
        type: str
    gateway_intf:
        description:
            - vsi view Gateway configuration interface
        required: false
        type: str
    gateway_subnet:
        description:
            - vsi view Gateway configuration subnet
        required: false
        type: str
    gateway_mask:
        description:
            - vsi view Gateway configuration subnet wild card mask
        required: false
        type: str
    vxlan:
        description:
            - Specify a Virtual eXtensible LAN
        required: false
        type: str
    encap:
        description:
            - Ethernet virtual private network module
        required: false
        type: bool
    rd:
        description:
            - Configure a route distinguisher
        required: false
        type: str
    vpn_target_auto:
        description:
            - Configure route targets
        required: false
        choices: ['both', 'export','import']
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
- name:  config vsi
  comware_vsi:
    vsi: vpna
    gateway_intf: Vsi-interface1
    gateway_subnet: 10.1.1.0
    gateway_mask: 0.0.0.255
    vxlan: 10
    encap: true
    rd: auto
    vpn_target_auto: both

- name: delete vsi configs
  comware_vsi:
    vsi: vpna
    state: absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.l2vpn import L2VPN
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vsi import Vsi
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.validate import valid_ip_network


def ip_stringify(**kwargs):
    return kwargs.get('gateway_subnet') + '/' + kwargs.get('gateway_mask')


def checks(existing, proposed, module):
    if existing.get('vsi') and proposed.get('vsi'):
        if proposed.get('vsi') != existing.get('vsi'):
            module.fail_json(msg='vxlan already assigned to another vsi.'
                                 + '\nremove it first.', vsi=existing.get('vsi'))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vsi=dict(required=True, type='str'),
            gateway_intf=dict(type='str'),
            gateway_subnet=dict(type='str'),
            gateway_mask=dict(type='str'),
            vxlan=dict(type='str'),
            encap=dict(type='bool'),
            rd=dict(type='str'),
            vpn_target_auto=dict(choices=['both', 'export', 'import'], type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    state = module.params['state']
    vsi = module.params['vsi']
    gateway_intf = module.params['gateway_intf']
    gateway_subnet = module.params['gateway_subnet']
    gateway_mask = module.params['gateway_mask']
    encap = module.params['encap']
    rd = module.params['rd']
    vpn_target_auto = module.params['vpn_target_auto']

    device = get_device(module)
    changed = False

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if state == 'present':
        if gateway_mask and gateway_subnet:
            if not valid_ip_network(ip_stringify(**module.params)):
                module.fail_json(msg='Not a valid IP address or mask.')

        if gateway_mask and not gateway_subnet:
            module.fail_json(msg='gateway_subnet and gateway_mask need to exist together')

        if gateway_subnet and not gateway_mask:
            module.fail_json(msg='gateway_subnet and gateway_mask need to exist together')

        if not encap:
            if rd or vpn_target_auto:
                module.fail_json(msg='RD and vpn target realized in evpn encapsulation vxlan view')

    is_l2vpn_enabled = 'disabled'
    try:
        l2vpn = L2VPN(device)
        is_l2vpn_enabled = l2vpn.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='L2VPN check failed')

    if is_l2vpn_enabled == 'disabled':
        module.fail_json(msg='l2vpn needs to be enabled.')

    if gateway_intf:
        interface = None
        try:
            interface = Interface(device, gateway_intf)
        except PYCW7Error:
            module.fail_json(msg='Error occurred while checking interface {0}'.format(gateway_intf))

        if not interface.iface_exists:
            module.fail_json(msg='The interface {0} is not exist'.format(gateway_intf))
    vsi_ins = None
    existing = []
    try:
        vsi_ins = Vsi(device, vsi)
        existing = vsi_ins.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='could not obtain existing')

    try:
        vsi_ins.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(e))

    if state == 'present':
        delta = proposed
        if delta:
            vsi_ins.build(stage=True, **delta)

    elif state == 'absent':
        delta = dict(vsi=vsi)
        if delta:
            vsi_ins.remove(stage=True, **delta)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            module.exit_json(mchanged=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = vsi_ins.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='failed during execution')
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
