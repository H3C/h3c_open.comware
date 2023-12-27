#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_vsi_intf
short_description: Configure some functions of vsi-interface
description:
    - Configure some functions of vsi-interface
version_added: 1.0.0
category: Feature (RW)
notes:
    - l2vpn needs to enabled before config vsi view.
    - vsi_intf must be vsi interface type , the module is only used for config vsi interface.
    - If you want to bind a interface with VPN instance, the VPN instance must be already exist.
options:
    vsi_intf:
        description:
            - The vsi interface view to config
        required: true
        type: str
    binding:
        description:
            - Bind the interface with a VPN instance
        required: false
        type: str
    macaddr:
        description:
            - config MAC address information
        required: false
        type: str
    local_proxy:
        description:
            - Enable local proxy ARP or ND function
        required: false
        choices: ['nd', 'arp']
        type: str
    distribute_gateway:
        description:
            - Specify the VSI interface as a distributed gateway
        required: false
        choices: ['local']
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
  - name: Config vsi interface
    h3c_open.comware.comware_vsi_intf:
      vsi_intf: Vsi-interface1
      binding: ali1
      macaddr: 01a-101a-40fa
      local_proxy: arp
      distribute_gateway: local
    register: results

  - name: Delete vsi interface
    h3c_open.comware.comware_vsi_intf:
      vsi_intf: Vsi-interface1
      binding: ali1
      state: absent
    register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.l2vpn import L2VPN
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vsi_intf import VsiInterface


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
            vsi_intf=dict(required=True, type='str'),
            binding=dict(type='str'),
            macaddr=dict(type='str'),
            local_proxy=dict(choices=['nd', 'arp'], type='str'),
            distribute_gateway=dict(choices=['local'], type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    state = module.params['state']
    vsi_intf = module.params['vsi_intf']
    binding = module.params['binding']

    device = get_device(module)
    changed = False

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)
    vsi_interface = None
    try:
        vsi_interface = Interface(device, vsi_intf)
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='could not obtain existing')

    if vsi_interface._iface_type(vsi_intf)[1] != 'Vsi-interface':
        module.fail_json(msg='This module is used for config vsi interface ' +
                             ', Other port types can be processed using the interface module')

    is_l2vpn_enabled = 'disabled'
    try:
        l2vpn = L2VPN(device)
        is_l2vpn_enabled = l2vpn.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='L2VPN check failed')

    if is_l2vpn_enabled == 'disabled':
        module.fail_json(msg='l2vpn needs to be enabled.')

    existing = []
    interface = None
    try:
        interface = VsiInterface(device, vsi_intf)
        existing = interface.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='could not obtain existing')

    if binding not in interface.get_vpn_config():
        module.fail_json(msg='The vpn-intance you provided does not exist, please create it first')

    try:
        interface.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(e))

    if state == 'present':
        delta = proposed
        if delta:
            interface.build(stage=True, **delta)

    elif state == 'absent':
        delta = dict(vsi=vsi_intf)
        if delta:
            interface.remove(stage=True, **delta)

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
                end_state = interface.get_config()
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
