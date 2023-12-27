#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_instance_rely
short_description: config instance rely ensure some instance configs can be set
description:
    - config instance rely ip vpn-instance and route-distinguisher 
version_added: 1.0.0
category: Feature (RW)
author: hanyangyang
notes:
    - some of the instance configs can be set before ip vpn-instance and route-distinguisher already 
      exists . 
    - state default or absent will make the device default config , if you want delete instance insance
      autonomous_system and instance_instance are both required . if  you want delete vpn_instance, 
      provide vpn_instance is OK.
options:     
    vpn_instance:
        description:
            - Name of the VPN instance
        required: True
        type: str
    vpn_instance_rd:
        description:
            - Route distinguisher, in the format ASN:nn or IP_address:nn
        required: False
        type: str
    address_family:
        description:
            - Address family
        required: False
        choices: ['evpn', 'ipv4', 'ipv6']
        type: str
    vpn_target:
        description:
            - Configure the Route Target attributes of the VPN instance
        required: False
        type: str
    vpn_target_mode:
        description:
            - The specified Route Target value is Import Target, Export Target or both.
        required: False
        choices: ['both', 'export', 'import']
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

- name: Create and config ip vpn-instance
  h3c_open.comware.comware_vpn_instance:
    vpn_instance: vpna
    vpn_instance_rd: '1:1'
    address_family: ipv4
    vpn_target: '2:2'
    vpn_target_mode: both
  register: results

- name: Create and config ip vpn-instance
  h3c_open.comware.comware_vpn_instance:
    vpn_instance: vpna
    vpn_instance_rd: '1:1'
    address_family: evpn
    vpn_target: '1:1'
    vpn_target_mode: both
  register: results

- name: Create and config ip vpn-instance
  h3c_open.comware.comware_vpn_instance:
    vpn_instance: vpna
    state: default
  register: results
        
"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vpn_instance import Instance
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vpn_instance=dict(required=True, type='str'),
            vpn_instance_rd=dict(type='str'),
            address_family=dict(choices=['evpn', 'ipv4', 'ipv6'], type='str'),
            vpn_target=dict(type='str'),
            vpn_target_mode=dict(choices=['both', 'export', 'import'], type='str'),
            state=dict(choices=['present', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    vpn_instance = module.params['vpn_instance']
    vpn_instance_rd = module.params['vpn_instance_rd']
    address_family = module.params['address_family']
    vpn_target = module.params['vpn_target']
    vpn_target_mode = module.params['vpn_target_mode']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    instance = None
    existing = []
    try:
        instance = Instance(device, vpn_instance)
    except PYCW7Error as e:
        module.fail_json(descr='there is problem in creating ip vpn-instance',
                         msg=str(e))

    try:
        instance.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(e))

    try:
        existing = instance.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        delta = proposed
        if delta:
            delta_vpn_instance = dict(vpn_instance=vpn_instance,
                                      vpn_instance_rd=vpn_instance_rd,
                                      address_family=address_family,
                                      vpn_target=vpn_target,
                                      vpn_target_mode=vpn_target_mode,
                                      )
            instance.build_vpn(stage=True, **delta_vpn_instance)

    elif state == 'default':
        delta_vpn_instance = dict(vpn_instance=vpn_instance)
        instance.remove_vpn(stage=True, **delta_vpn_instance)

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
                end_state = instance.get_config()
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
