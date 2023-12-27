#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_snmp_community
short_description: Manages SNMP community configuration on H3C switches.
description:
    - Manages SNMP community configuration on H3C switches.
version_added: 1.0.0
category: System (RW)
author: wangliang
options:
    acl_number:
        description:
            - Access control list number.
        required: false
        type: str
    community_name:
        description:
            - Unique name to identify the community.
        required: false
        type: str
    access_right:
        description:
            - Access right read or write.
        required: false
        choices: ['read','write']
        type: str
    community_mib_view:
        description:
            - Mib view name.
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
- name: "Config SNMP community"
  h3c_open.comware.comware_snmp_community: 
    state=present 
    access_right=read 
    community_mib_view=view 
    community_name=ansible_gqy 
    acl_number=3000

- name: "Undo SNMP community"
  h3c_open.comware.comware_snmp_community: 
    state=absent 
    access_right=write 
    community_mib_view=view 
    community_name=ansible_gqy 
    acl_number=3000
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.snmp_community import \
    SnmpCommunity


def param_check_snmp_community(**kwargs):
    """Basic param validation for snmp community.
    """
    module = kwargs["module"]
    community_name = module.params['community_name']
    access_right = module.params['access_right']
    community_mib_view = module.params['community_mib_view']
    acl_number = module.params['acl_number']
    if community_name and access_right:
        if len(community_name) > 32 or len(community_name) == 0:
            module.fail_json(
                msg='Error: The len of community_name %s is out of [1 - 32].' % community_name)

        if acl_number:
            if acl_number.isdigit():
                if int(acl_number) > 3999 or int(acl_number) < 2000:
                    module.fail_json(
                        msg='Error: The value of acl_number %s is out of [2000 - 3999].' % acl_number)
            else:
                if not acl_number[0].isalpha() or len(acl_number) > 32 or len(acl_number) < 1:
                    module.fail_json(
                        msg='Error: The len of acl_number %s is out of [1 - 32] or is invalid.' % acl_number)

        if community_mib_view:
            if len(community_mib_view) > 32 or len(community_mib_view) == 0:
                module.fail_json(
                    msg='Error: The len of community_mib_view %s is out of [1 - 32].' % community_mib_view)

    else:
        module.fail_json(
            msg='please provide community_name and access_right')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            acl_number=dict(type='str'),
            community_name=dict(type='str'),
            access_right=dict(choices=['read', 'write']),
            community_mib_view=dict(type='str', default='ViewDefault'),
        ),
        supports_check_mode=True
    )

    existing = dict()
    end_state = dict()
    changed = False

    filtered_keys = ('hostname', 'username', 'password', 'state',
                     'port', 'look_for_keys')

    state = module.params['state']
    community_name = module.params['community_name']

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    device = get_device(module)
    commands = None
    if community_name:
        snmp_community_obj = None
        try:
            snmp_community_obj = SnmpCommunity(device, community_name)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem recognizing that community_name.',
                             msg=str(e))

        try:
            param_check_snmp_community(module=module)
        except PYCW7Error as e:
            module.fail_json(
                descr='There was problem with the supplied parameters.',
                msg=str(e))

        try:
            existing = snmp_community_obj.get_config()
        except PYCW7Error as e:
            module.fail_json(msg=str(e),
                             descr='Error getting existing config.')

        if state == 'present':

            snmp_community_obj.create_build(stage=True, **proposed)
        elif state == 'absent':
            if existing:
                snmp_community_obj.community_remove(stage=True, **proposed)

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
                    end_state = snmp_community_obj.get_config()
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
