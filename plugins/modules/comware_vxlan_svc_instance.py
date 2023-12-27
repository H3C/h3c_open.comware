#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_vxlan_vsi
short_description: Manage mapping of an Ethernet Service to a VSI (VXLAN ID)
description:
  - Manage the mapping of an Ethernet Service to a VSI (VXLAN ID)
version_added: 1.0.0
category: Feature (RW)
notes:
  - VSI needs to be created before using this module (comware_vxlan)
  - encap and xconnect access_mode cannot be altered once set
    to change, use state=absent and re-configure
  - state=absent removes the service instance for specified interface if
    if it exists
  - This should be the last VXLAN module used after comware_vxlan_tunnel,
    and comware_vxlan.
options:
    vsi:
        description:
            - Name of the VSI
        required: false
        type: str
    interface:
        description:
            - Layer 2 interface or bridged-interface
        required: true
        type: str
    instance:
        description:
            - Service instance id
        required: true
        type: str
    encap:
        description:
            - only-tagged also ensures s-vid
        required: false
        default: default
        choices: ['default', 'tagged', 'untagged', 'only-tagged', 's-vid']
        type: str
    vlanid:
        description:
            - If encap is set to only-tagged or s-vid, vlanid must be set.
        required: false
        type: str
    access_mode:
        description:
            - Mapping Ethernet service instance to a VSI using Ethernet
              or VLAN mode (options for xconnect command)
        required: false
        default: vlan
        choices: ['ethernet', 'vlan']
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

# ensure the vsi is not mapped to the instance
- comware_vxlan_svc_instance: 
    interface: Fo1/0/32 
    vsi: VSI_VXLAN_100 
    instance: 100 
    state: absent

# ensure instance and vsi and configured with encap and access mode as specified
- comware_vxlan_svc_instance:
    interface: Fo1/0/32
    vsi: VSI_VXLAN_100
    instance: 100
    encap: default
    access_mode: vlan

# ensure instance and vsi and configured with encap and access mode as specified
- comware_vxlan_svc_instance:
    interface: Fo1/0/32
    vsi: VSI_VXLAN_100
    instance: 100
    encap: tagged
    access_mode: ethernet

# ensure instance and vsi and configured with encap and access mode as specified
- comware_vxlan_svc_instance:
    interface: Fo1/0/32
    vsi: VSI_VXLAN_100
    instance: 100
    encap: only-tagged
    vlanid: 10
    state: present
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.l2vpn import L2VPN
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vxlan import L2EthService


def checks(existing, proposed, module):
    if existing.get('encap') and proposed.get('encap'):
        if proposed.get('encap') != existing.get('encap'):
            module.fail_json(msg='cannot alter encap once set. remove '
                                 + '\ninstance and re-add')
    if existing.get('access_mode') and proposed.get('access_mode'):
        if proposed.get('access_mode') != existing.get('access_mode'):
            module.fail_json(msg='cannot alter mode once set. remove '
                                 + '\ninstance and re-add')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vsi=dict(required=True, type='str'),
            interface=dict(required=True, type='str'),
            instance=dict(required=True, type='str'),
            encap=dict(required=False, choices=['default', 'tagged',
                                                'untagged', 'only-tagged',
                                                's-vid'], default='default'),
            vlanid=dict(required=False, type='str'),
            access_mode=dict(required=False, choices=['ethernet', 'vlan'],
                             default='vlan'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    vsi = module.params['vsi']
    interface = module.params['interface']
    instance = module.params['instance']
    encap = module.params['encap']
    vlanid = module.params['vlanid']
    access_mode = module.params['access_mode']

    state = module.params['state']

    if encap in ['only-tagged', 's-vid']:
        if not vlanid:
            module.fail_json(msg='vlanid must be set when using only-tagged'
                                 + 'and s-vid as the encap')

    changed = False

    args = dict(encap=encap, vlanid=vlanid, access_mode=access_mode)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    is_l2vpn_enabled = 'disabled'
    try:
        l2vpn = L2VPN(device)
        is_l2vpn_enabled = l2vpn.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='L2VPN config check failed')

    if is_l2vpn_enabled == 'disabled':
        module.fail_json(msg='l2vpn needs to be enabled.')

    intf = None
    try:
        intf = Interface(device, interface)
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='could not instantiate interface')

    if intf.is_routed:
        module.fail_json(msg='interface needs to be an L2 interface')

    eth = None
    try:
        eth = L2EthService(device, interface, instance, vsi)
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='L2EthService failure')

    if not eth.vsi_exist():
        module.fail_json(msg='VSI needs to be created before using'
                             + ' this module')
    existing = {}
    try:
        existing = eth.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error getting L2EthService config')

    delta = dict(set(proposed.items()).difference(
        existing.items()))
    if state == 'present':
        if existing:
            checks(existing, proposed, module)

        if delta or not existing:
            eth.build(stage=True, **delta)
    elif state == 'absent':
        if existing:
            eth.remove(stage=True)

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
                end_state = eth.get_config()
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

    module.exit_json(**results)


if __name__ == "__main__":
    main()
