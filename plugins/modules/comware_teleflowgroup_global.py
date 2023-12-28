#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_teleflowgroup_global
short_description: Manage telemetry flow group agingtime on Comware 7 devices.The default value is Varies by device.
description:
    - Manage telemetry flow group agingtime on Comware 7 devices.The default value is Varies by device.
version_added: 1.0.0
author: gongqianyu(@gongqianyu)
options:
    agtime:
        description:
            - elemetry flow group agingtime
        required: true
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'default']
        type: str
"""

EXAMPLES = """
      - name: telemetry Flow Group aging time config
        h3c_open.comware.comware_teleflowgroup_global:
          agtime: 20
        register: results

      - name: config aging time into default state
        h3c_open.comware.comware_teleflowgroup_global:
          agtime: 20
          state: default
        register: results

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.teleflowgroup_global import \
    Flowglobal
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            agtime=dict(required=True, type='str'),
            state=dict(choices=['present', 'default'], default='present', type='str'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    agtime = module.params['agtime']
    state = module.params['state']

    changed = False

    args = dict(agtime=agtime)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    flowglobal = None
    existing = None
    try:
        flowglobal = Flowglobal(device, module, agtime, state)
        flowglobal.param_check()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    try:
        existing = flowglobal.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='error getting priority config')

    flow_global = None
    try:

        flow_global = Flowglobal(device, module=module)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error initialzing Switchport object.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            flow_global.build(state=state, stage=True, **delta)

    elif state == 'default':
        flow_global.default(state=state, stage=True)

    commands = None
    end_state = existing

    # if device state changed, ansible will be display result with 'changed', no change it will be ok.
    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            device.close()
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = flow_global.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='error during execution')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
