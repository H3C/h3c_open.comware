#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = '''
---

module: comware_compare
short_description: Enter the configuration command and compare it with the expected result.
description:
    - when input command,you need  In single quotes.
version_added: 1.0.0
author: gongqianyu(@gongqianyu)
notes:
    - This modules Enter the configuration command and compare it with the expected result.
      For convenience, put the expected result into a text, and enter the text path and name into the result parameter.
      if display ok,it is consistent.
options:
    cmd:
        description:
            - command.
        required: true
        type: str
    result:
        description:
            -  text path and name into the result parameter which include expected result .
        required: true
        type: str

'''
EXAMPLES = '''

  - name: Compare
    h3c_open.comware.comware_compare:
      cmd: 'dis curr conf | include vlan'
      result: '../result.txt'
    register: results

'''
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.compare import Compare


def main():
    module = AnsibleModule(
        argument_spec=dict(
            cmd=dict(required=True, type='str'),
            result=dict(required=True, type='str'),
        ),
        supports_check_mode=True
    )

    cmd = module.params['cmd']
    result = module.params['result']
    args = dict(cmd=cmd, result=result)
    device = get_device(module)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    changed = False
    commands = []

    COMPARE = Compare(device, cmd, result)

    check = COMPARE.get_result()

    if not check:
        module.fail_json(msg='compare result is Inconsistent!')

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
                                 descr='error during execution')
            changed = True

    results = {}
    results['commands'] = commands
    results['changed'] = changed
    results['proposed'] = proposed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
