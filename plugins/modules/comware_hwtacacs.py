#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_hwtacacs
short_description: Manage hwtacacs scheme
description:
    - Manage hwtacacs scheme
version_added: 1.0.0
category: Feature (RW)
author: hanyangyang
notes:
    - authentication host name can not set together with authentication ip
      authorization host name can not set together with authorization ip
      accounting host name can not set together with accounting ip
options:
    hwtacacs_scheme_name:
        description:
            - hwtacacs scheme name
        required: True
        type: str
    priority:
        description:
            - Specify the primary or secondary HWTACACS server
        required: false
        choices: ['primary', 'secondary']
        type: str
    auth_host_name:
        description:
            - Specify the primary HWTACACS authentication server name
        required: false
        type: str
    auth_host_ip:
        description:
            - authentication ip address
        required: false
        type: str
    auth_host_port:
        description:
            - port number, 49 by default
        required: false
        default: '49'
        type: str
    author_host_name:
        description:
            - Specify the primary HWTACACS authorization server name
        required: false
        default: '49'
        type: str
    author_host_ip:
        description:
            - authorization ip address
        required: false
        type: str
    author_host_port:
        description:
            - port number, 49 by default
        required: false
        default: '49'
        type: str
    acct_host_name:
        description:
            - Specify the primary HWTACACS accounting server name
        required: false
        type: str
    acct_host_ip:
        description:
            - accounting ip address
        required: false
        type: str
    acct_host_port:
        description:
            - port number, 49 by default
        required: false
        default: '49'
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
- name: config hwtacacs scheme
  h3c_open.comware.comware_hwtacacs:
    hwtacacs_scheme_name: test
    priority: primary
    auth_host_ip: 192.168.1.186
    auth_host_port: 48
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.hwtacacs import Hwtacacs


def main():
    module = AnsibleModule(
        argument_spec=dict(
            hwtacacs_scheme_name=dict(required=True),
            priority=dict(choices=['primary', 'secondary', ]),
            auth_host_name=dict(type='str'),
            auth_host_ip=dict(type='str'),
            auth_host_port=dict(type='str', default='49'),
            author_host_name=dict(type='str'),
            author_host_ip=dict(type='str'),
            author_host_port=dict(type='str', default='49'),
            acct_host_name=dict(type='str'),
            acct_host_ip=dict(type='str'),
            acct_host_port=dict(type='str', default='49'),
            state=dict(choices=['present', 'default', 'absent'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    hwtacacs_scheme_name = module.params['hwtacacs_scheme_name']
    priority = module.params['priority']

    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)
    hwtacacs_scheme = None
    try:
        hwtacacs_scheme = Hwtacacs(device, hwtacacs_scheme_name, priority)
    except PYCW7Error as e:
        module.fail_json(descr='there is problem in setting hwtacacs_scheme',
                         msg=str(e))
    if module.params['auth_host_name'] and module.params['auth_host_ip']:
        module.fail_json(msg='Only one of authentication name and ip is effective.')

    if module.params['author_host_name'] and module.params['author_host_ip']:
        module.fail_json(msg='Only one of authorization name and ip is effective.')

    if module.params['acct_host_name'] and module.params['acct_host_ip']:
        module.fail_json(msg='Only one of accounting name and ip is effective')

    if state == 'present':
        if not priority:
            if module.params['auth_host_name'] or module.params['auth_host_ip'] or \
                    module.params['author_host_name'] or module.params['author_host_ip'] or \
                    module.params['acct_host_name'] or module.params['acct_host_ip']:
                module.fail_json(msg='please assign priority ')

    try:
        hwtacacs_scheme.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(e))
    existing = {}
    try:
        existing = hwtacacs_scheme.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            delta_hwtacacs = dict(hwtacacs_scheme_name=hwtacacs_scheme_name)
            hwtacacs_scheme.build(stage=True, **delta_hwtacacs)
            hwtacacs_scheme.build_host_name_ip(stage=True, **delta)
    elif state == 'default' or state == 'absent':
        if hwtacacs_scheme_name:
            delta = dict(hwtacacs_scheme_name=hwtacacs_scheme_name)
            hwtacacs_scheme.default(stage=True, **delta)

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
                end_state = hwtacacs_scheme.get_config()
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
