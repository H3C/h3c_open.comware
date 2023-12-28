#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_sflow_intf
short_description: Manage sflow interface flow collector and sampling_rate on Comware 7 devices.
description:
    - Manage sflow interface flow collector and sampling_rate on Comware 7 devices.
version_added: 1.0.0
author: gongqianyu(@gongqianyu)
notes:
    - cli.  Netconf net surport.
options:
    intf_name:
        description:
            -  interface name.
        required: true
        type: str
    rate:
        description:
            -  Configure sampling_rate(>8192)
        required: false
        type: int
    collector:
        description:
            -  sflow flow collector(1~4).
        required: false
        default: 1
        choices: [1, 2, 3, 4]
        type: int
    state:
        description:
            - Desired state for the sflow configuration
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
"""

EXAMPLES = """
- name: netstream config
  comware_sflow_intf:
    intf_name: test
    rate: 1000
    collector: 2
- name: delete netstream config
  comware_sflow_intf:
    intf_name: test
    rate: 1000
    collector: 2
    state: absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.sflow_intf import Sflow
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            intf_name=dict(required=True, type='str'),
            collector=dict(required=False, type='int', choices=[1, 2, 3, 4], default=1),
            rate=dict(required=False, type='int'),
            state=dict(choices=['present', 'absent'], default='present', type='str'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    intf_name = module.params['intf_name']
    collector = module.params['collector']
    rate = module.params['rate']
    state = module.params['state']
    args = dict(collector=collector, rate=rate, intf_name=intf_name)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    changed = False
    sflow = None
    try:
        sflow = Sflow(device, intf_name, collector, rate)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    if state == 'present':
        sflow.build(stage=True)
    elif state == 'absent':
        sflow.remove(stage=True)

    commands = None

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
    results['state'] = state
    results['commands'] = commands
    results['changed'] = changed
    results['proposed'] = proposed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
