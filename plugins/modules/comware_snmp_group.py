#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_snmp_group
short_description: Manages SNMP group configuration on H3C switches.
description:
    - Manages SNMP group configuration on H3C switches.
version_added: 1.0.0
category: System (RW)
author: wangliang
options:
    acl_number:
        description:
            - Access control list number.
        required: false
        type: str
    version:
        description:
            - The security model by this user is provided.
        required: true
        type: str
    group_name:
        description:
            - Unique name for the group.
        required: false
        type: str
    security_level:
        description:
            - Security level indicating whether to use authentication and encryption.
        required: false
        choices: ['noAuthNoPriv', 'authentication']
        type: str
    read_view:
        description:
            - Mib view name for read.
        required: false
        type: str
    write_view:
        description:
            - Mib view name for write.
        required: false
        type: str
    notify_view:
        description:
            - Mib view name for notification.
        required: false
        type: str
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
        type: str
"""

EXAMPLES = """
  - name: Config SNMP group
    comware_snmp_group:
      state: present 
      version: v2c 
      group_name: wdz_group 
      security_level: noAuthNoPriv 
      acl_number: 2000
    
  - name: Undo SNMP group
    comware_snmp_group:
      state: absent  
      version: v2c 
      group_name: wdz_group 
      security_level: noAuthNoPriv 
      acl_number: 2000
      
  - name: Config SNMP V3 group
    comware_snmp_group:
      state: present 
      group_name: test_wl 
      version: v3 
      security_level: authentication  
      acl_number: 3000 
      write_view: 'testv3c'
        
  - name: Undo SNMP V3 group
    comware_snmp_group:
      state: absent 
      group_name: test_wl 
      version: v3 
      security_level: authentication  
      acl_number: 3000 
      write_view: 'testv3c'
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.snmp_group import SnmpGroup


def param_check_snmp_group(module):
    """Basic param validation for community snmp group

    Args:
        module: ansible module object
    """
    group_name = module.params['group_name']
    version = module.params['version']
    security_level = module.params['security_level']
    acl_number = module.params['acl_number']
    read_view = module.params['read_view']
    write_view = module.params['write_view']
    notify_view = module.params['notify_view']

    if group_name and version and security_level:
        if version != 'v3' and security_level != 'noAuthNoPriv':
            module.fail_json(
                msg='only v3 have another choice for security_level')

        if len(group_name) > 32 or len(group_name) == 0:
            module.fail_json(
                msg='Error: The len of group_name %s is out of [1 - 32].' % group_name)

        if acl_number:
            if acl_number.isdigit():
                if int(acl_number) > 3999 or int(acl_number) < 2000:
                    module.fail_json(
                        msg='Error: The value of acl_number %s is out of [2000 - 3999].' % acl_number)
            else:
                if not acl_number[0].isalpha() or len(acl_number) > 32 or len(acl_number) < 1:
                    module.fail_json(
                        msg='Error: The len of acl_number %s is out of [1 - 32] or is invalid.' % acl_number)

        if read_view:
            if len(read_view) > 32 or len(read_view) < 1:
                module.fail_json(
                    msg='Error: The len of read_view %s is out of [1 - 32].' % read_view)

        if write_view:
            if len(write_view) > 32 or len(write_view) < 1:
                module.fail_json(
                    msg='Error: The len of write_view %s is out of [1 - 32].' % write_view)

        if notify_view:
            if len(notify_view) > 32 or len(notify_view) < 1:
                module.fail_json(
                    msg='Error: The len of notify_view %s is out of [1 - 32].' % notify_view)
    else:
        module.fail_json(
            msg='please provide group_name, version and security_level')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            acl_number=dict(type='str'),
            group_name=dict(required=True, type='str'),
            version=dict(required=True, choices=['v1', 'v2c', 'v3']),
            security_level=dict(choices=['noAuthNoPriv', 'authentication', 'privacy'], default='noAuthNoPriv'),
            read_view=dict(type='str'),
            write_view=dict(type='str'),
            notify_view=dict(type='str'),
        ),
        supports_check_mode=True
    )

    existing = dict()
    end_state = dict()
    changed = False

    filtered_keys = ('hostname', 'username', 'password', 'state',
                     'port', 'look_for_keys')

    state = module.params['state']
    group_name = module.params['group_name']
    version = module.params['version']
    security_level = module.params['security_level']
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    device = get_device(module)

    commands = None
    if group_name:
        snmp_group_obj = None
        try:
            snmp_group_obj = SnmpGroup(device, group_name, version, security_level)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem recognizing that group_name.',
                             msg=str(e))

        try:
            param_check_snmp_group(module)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem with the supplied parameters.',
                             msg=str(e))

        try:
            existing = snmp_group_obj.get_config()
        except PYCW7Error as e:
            module.fail_json(msg=str(e),
                             descr='Error getting existing config.')

        if state == 'present':
            snmp_group_obj.group_build(stage=True, **proposed)
        elif state == 'absent':
            if existing:
                snmp_group_obj.group_remove(stage=True, **proposed)

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
                    end_state = snmp_group_obj.get_config()
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
