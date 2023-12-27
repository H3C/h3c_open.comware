#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_l2vpn_global
short_description: Manage global config state for L2VPN
description:
    - Enable or Disable L2VPN on a Comware 7 device
version_added: 1.0.0
category: Feature (RW)
options:
    state:
        description:
            - Desired state for l2vpn global configuration
        required: true
        choices: ['enabled', 'disabled']
        type: str
"""
EXAMPLES = """

  - name: Enable l2vpn globally
    h3c_open.comware.comware_l2vpn_global:
      state: enabled
    register: results

  - name: Disable l2vpn globally
    h3c_open.comware.comware_l2vpn_global:
      state: disabled
    register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.l2vpn import L2VPN


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['enabled', 'disabled'], required=True, type='str'),
        ),
        supports_check_mode=True
    )
    device = get_device(module)
    state = module.params['state']
    changed = False
    existing = "disabled"
    l2vpn = None
    try:
        l2vpn = L2VPN(device)
        existing = l2vpn.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error getting existing config')

    if existing != state:
        if state == 'enabled':
            l2vpn.config(stage=True)
        elif state == 'disabled':
            l2vpn.disable(stage=True)

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
                end_state = l2vpn.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')
            changed = True

    results = {}
    results['proposed'] = state
    results['existing'] = existing
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = end_state
    module.exit_json(**results)


if __name__ == "__main__":
    main()
