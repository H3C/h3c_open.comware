#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_ftp
short_description: Configure device FTP function.
description:
    -Configure device FTP function.
version_added: 1.0.0
author: liudongxue(@liudongxue)
notes:
    - When using the FTP function of the device,you need to enable FTP first.
options:
    state:
        description:
            - The state of FTP
        required: false
        default: disable
        choices: ['enable', 'disable']
        type: str
"""
EXAMPLES = """
- name: Enabling FTP
  h3c_open.comware.comware_ftp:
    state: enable
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.ftp import Ftp


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['enable', 'disable'],
                       default='disable'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    changed = False

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    ftp = Ftp(device, state)
    ftp.config_ftp(stage=True)
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
