#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_bfd
short_description: Management configuration bfd function
description:
    - Manage bfd config
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - This module is currently only used to enable BFD session flapping suppression ,
      other functions depend on other protocols and are not yet available.
    - Bfd dampening maximum delay and initial delay are required , also the second interval.
    - The initial interval and second interval must be shorter than the maximum interval.
    - Maximum , initial and second interval are required in 1-3600 seconds.

options:
    damp_max_wait_time:
        description:
            - Configure the maximum dampening timer interval
        required: false
        type: str
    damp_init_wait_time:
        description:
            - Configure the initial dampening timer interval
        required: false
        type: str
    secondary:
        description:
            - Configure the second dampening timer interval
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        choices: ['present', 'default']
        default: present
        type: str

"""
EXAMPLES = """

      - name: config bfd
        h3c_open.comware.comware_bfd:
          damp_max_wait_time: 100
          damp_init_wait_time: 10
          secondary: 8

      - name: delete bfd related
        h3c_open.comware.comware_bfd:
          damp_max_wait_time: 100
          damp_init_wait_time: 10
          secondary: 8
          state: default

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.bfd import Bfd
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            damp_max_wait_time=dict(type='str'),
            damp_init_wait_time=dict(type='str'),
            secondary=dict(type='str'),
            state=dict(choices=['present', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    damp_max_wait_time = module.params['damp_max_wait_time']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if damp_max_wait_time:
        if not module.params.get('damp_init_wait_time'):
            safe_fail(module, msg='damp_init_wait_time is required for bfd dampening config')
        else:
            if not module.params['secondary']:
                safe_fail(module, msg='secondary is required for bfd dampening config')
    bfd = None
    try:
        bfd = Bfd(device, )
    except PYCW7Error as exe:
        safe_fail(module, descr='there is problem in setting localuser',
                  msg=str(exe))

    existing = None
    try:
        existing = bfd.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting existing config.')

    if state == 'present':
        if existing:
            delta = dict(set(proposed.items()).difference(
                existing.items()))
        else:
            delta = proposed
        if delta:
            bfd.build(stage=True, **delta)

    elif state == 'default':
        bfd.default(stage=True, )

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
                end_state = bfd.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
