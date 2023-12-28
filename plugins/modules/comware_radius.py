#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_radius
short_description: create radius scheme
description:
    - create radius scheme
version_added: 1.0.0
author: hanyangyang (@hanyangyang)
notes:
options:
    radius_scheme:
        description:
            - Specify RADIUS scheme
        required: True
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

  - name: Basic radius config
    h3c_open.comware.comware_radius:
      radius_scheme: test
    register: results

  - name: Delete radius config
    h3c_open.comware.comware_radius:
      radius_scheme: test
      state: default
    register: results

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.radius import Radius


def main():
    module = AnsibleModule(
        argument_spec=dict(
            radius_scheme=dict(required=True, type='str'),
            state=dict(choices=['present', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    radius_scheme = module.params['radius_scheme']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    radius = None
    existing = []
    existing_radius = []
    try:
        radius = Radius(device, radius_scheme)
    except PYCW7Error as e:
        module.fail_json(descr='there is problem in setting localuser',
                         msg=str(e))
    try:
        existing = radius.get_config()
        existing_radius = radius.get_radius_info()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            radius.build(stage=True, **delta)

    elif state == 'default':
        if radius_scheme in existing_radius:
            delta = dict(radius_scheme=radius_scheme)
            radius.default(stage=True, **delta)

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
                end_state = radius.get_config()
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
