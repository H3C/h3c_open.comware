#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_telemetryflowtrace
short_description: Manage Package information of the message sent to the collector on V7 devices
description:
    - Manage Package information of the message sent to the collector on V7 devices
version_added: 1.0.0
author: gongqianyu(@gongqianyu)
notes:
    - If state=absent, the config will be removed
options:
    sourceID:
        description:
            - The source IP address of the packet package of the uplink collector
        required: True
        type: str
    destinID:
        description:
            - Destination IP address of the packet package of the uplink collector
        required: True
        type: str
    sourcePort:
        description:
            - The source port number of the message package of the up sending collector.
        required: True
        type: str
    destinPort:
        description:
            - Destination port number of the message package of the uplink collector.
        required: True
        type: str
    state:
        description:
            - Desired state of the switch port
        required: false
        default: present
        choices: ['present', 'absent']
        type: str


"""
EXAMPLES = """

      - name: telemetryflowtrace basic config
        h3c_open.comware.comware_telemetryflowtrace:
          sourceID: 10.10.10.1
          destinID: 10.10.10.2
          sourcePort: 10
          destinPort: 30
        register: results

      - name: telemetryflowtrace delete config
        h3c_open.comware.comware_telemetryflowtrace:
          sourceID: 10.10.10.1
          destinID: 10.10.10.2
          sourcePort: 10
          destinPort: 30
          state: absent
        register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.telemetryflowtrace import (
    Telemetry)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            sourceID=dict(required=True, type='str'),
            destinID=dict(required=True, type='str'),
            sourcePort=dict(required=True, type='str'),
            destinPort=dict(required=True, type='str'),

            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'look_for_keys')

    device = get_device(module)

    sourceID = module.params['sourceID']
    destinID = module.params['destinID']
    sourcePort = module.params['sourcePort']
    destinPort = module.params['destinPort']

    state = module.params['state']

    args = dict(sourceID=sourceID, destinID=destinID, sourcePort=sourcePort, destinPort=destinPort)
    proposed = dict((k, v) for k, v in args.items() if v is not filtered_keys)
    changed = False

    telemetry = None
    existing = None
    try:

        telemetry = Telemetry(device, sourceID, destinID, sourcePort, destinPort)
    #       telemetry.param_check(**proposed)
    #        telemetry = Telemetry(device)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    try:
        existing = telemetry.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting telemetry config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(existing.items()))
        if delta:
            telemetry.build(stage=True)

    elif state == 'absent':
        if existing:
            telemetry.remove(stage=True)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = telemetry.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error during command execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
