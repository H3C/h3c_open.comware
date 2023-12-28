#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_command
short_description: Execute CLI commands on Comware 7 devices
description:
    - Execute CLI commands on Comware 7 devices
version_added: 1.0.0
author: liudongxue(@liudongxue)
notes:
    - This module is not idempotent
options:
    type:
        description:
            - State whether the commands are display (user view)
              or configure (system view) commands.  Display and
              show are the same thing.
        required: false
        choices: ['display', 'config', 'show']
        type: str
    command:
        description:
            - String (single command) or list of commands to be
              executed on the device.  Sending a list requires
              YAML format to be used in the playbook.
        required: false
        type: list
        elements: str
    file_txt:
        description:
            - Text file on server.
              Include file path and file name.
        required: false
        type: str
"""

EXAMPLES = """

- name: Display vlan 5 passing in a string
  h3c_open.comware.comware_command:
    command: 'display vlan 5'
    type: display
  register: results

- name: Execute command by using file
  h3c_open.comware.comware_command:
    file_txt: /root/test.txt
    type: config
  register: results

- name: Display vlans passing in a list
  h3c_open.comware.comware_command:
    command:
      - display vlan 10
      - display vlan 5
    type: display
  register: results

- name: Passing in config commands as a list
  h3c_open.comware.comware_command:
    command:
      - vlan 5
      - name web_vlan
    type: config
  register: results
"""
from ansible.module_utils._text import to_text
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import \
    PYCW7Error, ConnectionError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device, get_connection, get_capabilities
)


def file_list(file):
    fp = open(str(file), 'rb')
    txt = str(fp.read(), 'utf-8')
    txt_list = txt.split('\n')
    commandlist = [x for x in txt_list if x != '']
    return commandlist


def main():
    module = AnsibleModule(
        argument_spec=dict(
            type=dict(required=False, choices=['display', 'show', 'config'], type='str'),
            command=dict(required=False, type='list', elements='str'),
            file_txt=dict(required=False, type='str'),
        ),
        supports_check_mode=True
    )

    conn = get_connection(module)
    capabilities = get_capabilities(module)
    command = module.params['command']

    if capabilities.get("network_api") == "cliconf":
        if any(
                (
                    module.params['type'],
                    module.params['file_txt'],
                ),
        ):
            module.warn(
                "arguments type, file_txt are not supported when using transport=cli",
            )

        output = list()
        for cmd in command:
            try:
                output.append(conn.get(command=cmd))
            except ConnectionError as exc:
                module.fail_json(
                    msg=to_text(exc, errors="surrogate_then_replace"),
                )

        lines = [out.split("\n\n") for out in output]
        results = {"changed": False, "stdout": output, "stdout_lines": lines}
        module.exit_json(**results)

    if not module.params.get('type'):
        module.fail_json(
            msg="need arguments type when using transport=netconf",
        )

    device = get_device(module)
    ctype = module.params['type']
    file_txt = module.params['file_txt']
    if file_txt:
        command = file_list(file_txt)
    changed = False

    proposed = dict(type=ctype, command=command)
    response = None
    if isinstance(command, list):
        config_string = ';'.join(command)

    else:
        config_string = command

    if module.check_mode:
        module.exit_json(changed=True,
                         config_string=config_string)

    try:
        if ctype in ['show', 'display']:
            response = device.cli_display(command)
        elif ctype in ['config']:
            response = device.cli_config(command)
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error during execution')

    res_by_line = response.split('\n')

    changed = True

    results = {}
    results['proposed'] = proposed
    results['config_string'] = config_string
    results['changed'] = changed
    results['end_state'] = 'N/A for this module.'
    results['response'] = res_by_line

    module.exit_json(**results)


if __name__ == "__main__":
    main()
