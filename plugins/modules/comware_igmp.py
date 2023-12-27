#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_igmp
short_description: Configure the igmp issue to be applied to the interface.
description:
    -Configure the acl igmp to be applied to the interface.
version_added: 1.0.0
category: Feature (RW)
author: liudongxue
notes:
    - When configuring IGMP,the interface must be a routing interface.
    - Parameter 'name' is required when deleting IGMP.

options:
    name:
        description:
            - Full name of the interface
        required: false
        type: str
    igstate:
        description:
            - The status of IGMP
        required: false
        choices: ['enabled', 'disabled']
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
    version:
        description:
            - The version of IGMP
        required: false
        default: version2
        choices: ['version1', 'version2', 'version3']
        type: str
    snstate:
        description:
            -  The state of igmp-snooping 
        required: false
        default: disable
        choices: ['enable', 'disable']
        type: str
    mode:
        description:
            - The mode of PIM
        required: false
        choices: ['sm', 'dm']
        type: str
"""
EXAMPLES = """
  - name: create IGMP and configure IGMP version
    comware_igmp: 
      name: Twenty-FiveGigE1/0/22 
      igstate: enabled 
      version: version1 
      state: present
  - name: delete IGMP ,delete IGMP version
    comware_igmp: 
      name: Twenty-FiveGigE1/0/22 
      igstate: disabled 
      state: absent 
  - name: configure PIM mode
    comware_igmp: 
      name: Twenty-FiveGigE1/0/22 
      mode: dm 
      state: present
  - name: delete PIM mode
    comware_igmp: 
      name: Twenty-FiveGigE1/0/22 
      mode: dm 
      state: absent
  - name: configure IMGP-Snooping
    comware_igmp: 
      snstate: enable 
      state: present
  - name: delete IMGP-Snooping
    comware_igmp: 
      snstate: disable 
      state: absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    PYCW7Error, InterfaceAbsentError)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.igmp import Igmp


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str'),
            igstate=dict(choices=['enabled', 'disabled']),
            state=dict(choices=['present', 'absent'],
                       default='present'),
            version=dict(choices=['version1', 'version2', 'version3'],
                         default='version2'),
            snstate=dict(choices=['enable', 'disable'],
                         default='disable'),
            mode=dict(choices=['sm', 'dm']),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)

    state = module.params['state']
    igstate = str(module.params['igstate'])
    mode = module.params['mode']
    snstate = module.params['snstate']
    changed = False

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)
    interface = None
    if module.params.get('name'):
        name = module.params.get('name')
        try:
            interface = Interface(device, name)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem recognizing that interface.',
                             msg=str(e))
    else:
        name = ''
        try:
            interface = Interface(device, name)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem recognizing that interface.',
                             msg=str(e))
    is_ethernet, is_routed = interface.is_ethernet_is_routed()
    if state == 'present':
        if igstate == 'enabled':
            if name == '':
                module.fail_json(msg='The \'igstate\' parameter must be compatible with:'
                                     '\nname.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
            else:
                if is_ethernet:
                    module.fail_json(msg='The interface type must be a routing mode.'
                                         '\nPlease configure type first by itself,'
                                         '\nthen run again.')
        if module.params.get('mode'):
            mode = module.params.get('mode')
            if name == '':
                module.fail_json(msg='The \'mode\' parameter must be compatible with:'
                                     '\nname.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
            else:
                if is_ethernet:
                    module.fail_json(msg='The interface mode must be route.'
                                         '\nPlease configure type first by itself,'
                                         '\nthen run again.')
    if state == 'absent' and snstate != 'disable':
        if name == '':
            module.fail_json(msg='The \'name\' parameter must be set.'
                                 '\nPlease configure type first by itself,'
                                 '\nthen run again.')
    igmp = Igmp(device, name)
    # config igmp snooping
    if name == '':
        if snstate == 'enable':
            igmp.build_igmp_snooping(stage=True, snstate=snstate)
        if snstate == 'disable':
            igmp.build_igmp_snooping(stage=True, snstate=snstate)
    else:
        if state == 'present':
            if is_routed:
                if igstate == 'enabled':
                    args = dict(igstate=str(module.params.get('igstate')), version=str(module.params.get('version')))
                    igmp.build_igmp(stage=True, **args)
                if mode:
                    args = dict(mode=str(module.params.get('mode')))
                    igmp.config_pim_mode(stage=True, **args)
            else:
                raise InterfaceAbsentError(name)

        elif state == 'absent':
            if is_routed:
                if igstate == 'disabled':
                    igmp.remove_igmp(stage=True)
                if mode:
                    igmp.remove_pim_mode(stage=True)
            else:
                raise InterfaceAbsentError(name)

    existing = True
    commands = None
    end_state = True

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
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
