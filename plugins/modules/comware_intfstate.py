#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = '''
---

module: comware_intfstate
short_description: Check the port status. If there are undo shutdown ports but the field ports are down,
                   list these inconsistent ports. If not, return OK.
description:
    - .
version_added: 1.0.0
author: gongqianyu(@gongqianyu)

'''
EXAMPLES = '''

      - name: Check the port status
        comware_intfstate:

'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.intfstate import IntfState


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(),
        supports_check_mode=True
    )

    device = get_device(module)

    changed = False
    commands = []

    compare = IntfState(device)

    check = compare.get_result()
    if not check:
        module.fail_json(msg=check)
    else:
        pass

    if device.staged:

        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='error during execution')
            changed = True

    results = {'commands': commands, 'changed': changed}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
