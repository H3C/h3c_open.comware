#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_local_user
short_description: Manage local_user
description:
    - Manage local_user
version_added: 1.0.0
category: Feature (RW)
author: hanyangyang
notes:
    - Before using ftp_dir , ensure it already exist in the device.
    - Local user group specify the user group , if the device has the group then do the config, 
        if not, create group and config
options:
    localusername:
        description:
            - Local user name
        required: True
        type: str
    group:
        description:
            - User group name
        required: false
        type: str
    server_ftp:
        description:
            - enable or disable local user service-type ftp
        required: false
        choices: ['true', 'false']
        type: str
    server_http:
        description:
            - enable or disable local user service-type http
        required: false
        choices: ['true', 'false']
        type: str
    server_https:
        description:
            - enable or disable local user service-type https
        required: false
        choices: ['true', 'false']
        type: str
    server_pad:
        description:
            - enable or disable local user service-type pad
        required: false
        choices: ['true', 'false']
        type: str
    server_ssh:
        description:
            - enable or disable local user service-type ssh
        required: false
        choices: ['true', 'false']
        type: str
    server_telnet:
        description:
            - enable or disable local user service-type telnet
        required: false
        choices: ['true', 'false']
        type: str
    server_Terminal:
        description:
            - enable or disable local user service-type terminal
        required: false
        choices: ['true', 'false']
        type: str
    ftp_dir:
        description:
            - Specify work directory of local user
        required: false
        choices: ['true', 'false']
        type: str
    local_user_level:
        description:
            - Specify local user work level
        required: false
        type: str
    localspassword:
        description:
            - Password used to login to the local user
        required: false
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
- name: Basic Ethernet config
  h3c_open.comware.comware_local_user:
    localusername: test123
    server_ftp: True
    local_user_level: 15
"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.localuser import LocalUser


def main():
    module = AnsibleModule(
        argument_spec=dict(
            localusername=dict(required=True, type='str'),
            group=dict(type='str'),
            server_ftp=dict(type='str', choices=['true', 'false'], default='false'),
            server_http=dict(type='str', choices=['true', 'false'], default='false'),
            server_https=dict(type='str', choices=['true', 'false'], default='false'),
            server_pad=dict(type='str', choices=['true', 'false'], default='false'),
            server_ssh=dict(type='str', choices=['true', 'false'], default='false'),
            server_telnet=dict(type='str', choices=['true', 'false'], default='false'),
            server_Terminal=dict(type='str', choices=['true', 'false'], default='false'),
            ftp_dir=dict(type='str'),
            local_user_level=dict(type='str'),
            localspassword=dict(type='str'),
            state=dict(type='str', choices=['present', 'default'],
                       default='present')
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    localusername = module.params['localusername']
    server_ftp = module.params['server_ftp']
    server_http = module.params['server_http']
    server_https = module.params['server_https']
    server_pad = module.params['server_pad']
    server_ssh = module.params['server_ssh']
    server_telnet = module.params['server_telnet']
    server_Terminal = module.params['server_Terminal']
    local_user_level = module.params['local_user_level']
    group = module.params['group']

    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if server_ftp == 'True':
        if server_http or server_https or server_pad or \
                server_ssh or server_telnet or server_Terminal:
            module.fail_json(msg="local user can't be this in ['http'\
                                'https','pad','ssh','telnet','terminal'] \
                                while ftp has been set")
    local_user = None
    try:
        local_user = LocalUser(device, localusername)
    except PYCW7Error as e:
        module.fail_json(descr='there is problem in setting localuser',
                         msg=str(e))

    try:
        local_user.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(e))
    existing_groups = []
    existing = {}
    try:
        existing = local_user.get_config()
        existing_groups = local_user.get_group_info()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        if group in existing_groups or group is None:
            pass
        else:
            local_user.build_group(stage=True, group=group)
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            if local_user_level:
                del proposed['local_user_level']
                local_user.build(stage=True, **proposed)
                delta_level = dict(localusername=localusername,
                                   local_user_level=local_user_level)
                local_user.build_user_level(stage=True, **delta_level)
            else:
                local_user.build(stage=True, **proposed)

    elif state == 'default':
        if localusername:
            delta = dict(localusername=localusername)
            local_user.default(stage=True, **delta)

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
                end_state = local_user.get_config()
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
