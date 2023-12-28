#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_lldp_global
short_description: Manage global config state for LLDP.this funtion can be take effect only global \
                   and interface LLDP all open.
                   The interface LLDP is open default.
description:
    - Enable or Disable global LLDP on a Comware 7 device
author: gongqianyu(@gongqianyu)
version_added: 1.0.0
options:
    state:
        description:
            - Desired state for LLDP global configuration
        required: true
        choices: ['enabled', 'disabled']
        type: str

"""

EXAMPLES = """

  - name: Manage lldp global enable
    h3c_open.comware.comware_lldp_global:
      state: enabled
    register: results

  - name: Manage lldp global disable
    h3c_open.comware.comware_lldp_global:
      state: disabled
    register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.lldp_global import LLDP


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['enabled', 'disabled'], required=True),
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    state = module.params['state']
    changed = False
    args = dict(state=state)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    lldp = None
    existing = []
    try:
        lldp = LLDP(device)
        existing = lldp.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error getting existing config')

    if existing != state:
        if state == 'enabled':
            lldp.enable(stage=True)
        elif state == 'disabled':
            lldp.disable(stage=True)

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
                end_state = lldp.get_config()
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
