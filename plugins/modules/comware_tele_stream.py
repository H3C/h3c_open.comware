#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_tele_stream
short_description: Manage telemetry global enable(disable) and telemetry stream timestamp enable(disable) and device-id
                   on Comware 7 devices.Before config device-id,the timestamp must be enable.
description:
    - Manage telemetry global enable(disable) and telemetry stream timestamp enable(disable) and device-id
      on Comware 7 devices.Before config device-id,the timestamp must be enable.
version_added: 1.0.0
author: gongqianyu(@gongqianyu)
options:
    glo_enable:
        description:
            - config global telemetry stream enable.The default state is enable.
        required: false
        default: enable
        choices: ['enable', 'disable']
        type: str
    timestamp:
        description:
            - config telemetry stream timestamp enable.The default state is disable.
        required: false
        default: disable
        choices: ['enable', 'disable']
        type: str
    deviceID:
        description:
            - config telemetry stream device-id.
        required: false
        type: str
    state:
        description:
            - Recovering the default state of telemetry stream
        required: false
        default: present
        choices: ['present', 'default']
        type: str
"""

EXAMPLES = """

- name: telemetry config
  h3c_open.comware.comware_tele_stream:
    glo_enable: enable
    timestamp: enable
    deviceID: 10.10.10.1
    state: present
  register: results


- name: remove telemetry
  h3c_open.comware.comware_tele_stream:
    glo_enable: enable
    timestamp: enable
    deviceID: 10.10.10.1
    state: default
  register: results

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.tele_stream import Telemetry
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            timestamp=dict(required=False, choices=['enable', 'disable'], default='disable', type='str'),
            glo_enable=dict(required=False, choices=['enable', 'disable'], default='enable', type='str'),
            deviceID=dict(required=False, type='str'),
            state=dict(required=False, choices=['present', 'default'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    timestamp = module.params['timestamp']
    glo_enable = module.params['glo_enable']
    state = module.params['state']
    deviceID = module.params['deviceID']

    changed = False

    args = dict(timestamp=timestamp, glo_enable=glo_enable, deviceID=deviceID)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    telemetry = None
    try:
        telemetry = Telemetry(device)
    #        existing = telemetry.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    if state == 'present':
        telemetry.build(stage=True, timestamp=timestamp, glo_enable=glo_enable, deviceID=deviceID)

    elif state == 'default':
        telemetry.remove(stage=True, timestamp=timestamp, glo_enable=glo_enable, deviceID=deviceID)

    commands = None
    #    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
            #               end_state = telemetry.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='error during execution')
            changed = True

    results = {'proposed': proposed, 'state': state, 'commands': commands, 'changed': changed}
    #    results['end_state'] = end_state

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
