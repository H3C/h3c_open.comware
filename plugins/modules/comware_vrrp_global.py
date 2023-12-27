#!/usr/bin/python


DOCUMENTATION = """
---

module: comware_vrrp_global
short_description: Manage VRRP global configuration mode
description:
    - Manage VRRP global configuration mode
version_added: 1.0.0
category: Feature (RW)
options:
    mode:
        description:
            - vrrp config mode for the switch
        required: true
        choices: ['standard', 'load-balance']
        type: str

"""
EXAMPLES = """

  - name: Vrrp global config mode - standard
    h3c_open.comware.comware_vrrp_global:
      mode: standard
    register: data

  - assert:
      that:
        - data.end_state == 'standard'

  - name: Vrrp global config mode - LB
    h3c_open.comware.comware_vrrp_global:
      mode: load-balance
    register: data

  - assert:
      that:
        - data.end_state == 'load-balance'

  - name: Revert back
    h3c_open.comware.comware_vrrp_global:
      mode: standard
    register: data

  - assert:
      that:
        - data.end_state == 'standard'
        - data.changed == true

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def get_existing(device):
    rsp = device.cli_display('display vrrp verbose').split('\n')
    existing_mode = 'unknown'
    for line in rsp:
        if 'mode' in line:
            existing_mode = line.split(':')[-1].strip().lower()
            if existing_mode == 'load balance':
                existing_mode = 'load-balance'
    return existing_mode


def main():
    module = AnsibleModule(
        argument_spec=dict(
            mode=dict(required=True, choices=['load-balance', 'standard'], type='str'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    mode = module.params['mode']
    changed = False
    delta = False

    existing = []
    command = None
    try:
        existing = get_existing(device)
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error getting existing config')

    end_state = existing
    if existing != mode:
        delta = True

    if delta:
        if mode == 'load-balance':
            command = 'vrrp mode {0}'.format(mode)
        elif mode == 'standard':
            command = 'undo vrrp mode'
        device.stage_config(command, "cli_config")

    commands = None
    response = None

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            device.close()
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                response = device.execute_staged()
                end_state = get_existing(device)
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')

            changed = True

    results = {}
    results['proposed'] = mode
    results['existing'] = existing
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = end_state
    results['response'] = response

    module.exit_json(**results)


if __name__ == "__main__":
    main()
