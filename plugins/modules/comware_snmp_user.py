#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_snmp_user
short_description: Manages SNMP user configuration on H3c switches.
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
        type: int
    usm_user_name:
        description:
            - Unique name for the user.
        required: true
        type: str
    user_group:
        description:
            - Unique name for the user group.
        required: true
        type: str
    security_model:
        description:
            - The security model by this user is provided.
        required: true
        choices: ['v1', 'v2c', 'v3']
        type: str
    auth_protocol:
        description:
            - Authentication algorithm.
        required: false
    priv_protocol:
        description:
            - Encryption algorithm privacy.
        required: false
        type: str
    auth_key:
        description:
            - Authentication key.
        required: false
        type: str
    priv_key:
        description:
            - Privacy key.
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
  - name: Config SNMP v3 User
    h3c_open.comware.comware_snmp_user:
      state: present 
      usm_user_name: gtest_w_ansible 
      security_model: v3 
      user_group: gtest_w_ansible 
      auth_protocol: sha 
      priv_protocol: 3des 
      auth_key: gtest_w_ansible 
      priv_key: gtest_w_ansible

  - name: Undo SNMP v3 User
    h3c_open.comware.comware_snmp_user:
      state: absent 
      usm_user_name: gtest_w_ansible 
      security_model: v3 
      user_group: gtest_w_ansible 
      auth_protocol: sha 
      priv_protocol: 3des 
      auth_key: gtest_w_ansible 
      priv_key: gtest_w_ansible
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.snmp_user import SnmpUser


def param_check_snmp_user(module):
    """Basic param validation for snmp user

    Args:
        module (AnsibleModule): module object
    """

    usm_user_name = module.params['usm_user_name']
    user_group = module.params['user_group']
    security_model = module.params['security_model']
    acl_number = module.params['acl_number']
    auth_protocol = module.params['auth_protocol']
    priv_protocol = module.params['priv_protocol']

    if usm_user_name and security_model:
        if security_model != 'v3' and auth_protocol:
            module.fail_json(
                msg='only v3 have auth_protocol config')

        if security_model != 'v3' and priv_protocol:
            module.fail_json(
                msg='only v3 have priv_protocol config')

        if len(user_group) > 32 or len(user_group) == 0:
            module.fail_json(
                msg='Error: The len of user_group %s is out of [1 - 32].' % user_group)

        if acl_number:
            if acl_number.isdigit():
                if int(acl_number) > 3999 or int(acl_number) < 2000:
                    module.fail_json(
                        msg='Error: The value of acl_number %s is out of [2000 - 3999].' % acl_number)
            else:
                if not acl_number[0].isalpha() or len(acl_number) > 32 or len(acl_number) < 1:
                    module.fail_json(
                        msg='Error: The len of acl_number %s is out of [1 - 32] or is invalid.' % acl_number)
    else:
        module.fail_json(
            msg='please provide usm_user_name and security_model at least')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            acl_number=dict(type='str'),
            usm_user_name=dict(required=True, type='str'),
            user_group=dict(required=True, type='str'),
            security_model=dict(required=True, choices=['v1', 'v2c', 'v3']),
            auth_protocol=dict(choices=['md5', 'sha']),
            priv_protocol=dict(choices=['3des', 'aes128', 'aes192', 'aes256', 'des56']),
            auth_key=dict(type='str'),
            priv_key=dict(type='str'),
        ),
        supports_check_mode=True
    )

    existing = dict()
    end_state = dict()
    changed = False

    filtered_keys = ('hostname', 'username', 'password', 'state',
                     'port', 'look_for_keys')

    state = module.params['state']
    usm_user_name = module.params['usm_user_name']
    user_group = module.params['user_group']
    security_model = module.params['security_model']
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    device = get_device(module)
    commands = None
    if usm_user_name:
        snmp_user_obj = None
        try:
            snmp_user_obj = SnmpUser(device, usm_user_name, user_group, security_model)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem recognizing that usm_user_name.',
                             msg=str(e))

        try:
            param_check_snmp_user(module=module)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem with the supplied parameters.',
                             msg=str(e))

        try:
            existing = snmp_user_obj.get_config()
        except PYCW7Error as e:
            module.fail_json(msg=str(e),
                             descr='Error getting existing config.')

        if state == 'present':
            # delta = dict(set(proposed.iteritems()).difference(
            #     existing.iteritems()))
            # if delta:
            snmp_user_obj.user_build(stage=True, **proposed)
        elif state == 'absent':
            if existing:
                snmp_user_obj.user_remove(stage=True, **proposed)

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
                    end_state = snmp_user_obj.get_config()
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
