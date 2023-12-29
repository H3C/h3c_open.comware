#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_irf_ports
short_description: Manage IRF port creation and removal for Comware v7 devices
description:
    - Manage IRF port creation and removal for Comware v7 devices
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - This module is meant to be run after the comware_irf_members module.
    - The process is as follows 1) Use comware_irf_members to change
      the IRF member identity of the device, with the reboot=true
      flag, or reboot the device through some other means. 2) Use
      comware_irf_members to change priority, description, and domain,
      if desired. 3) Use the comware_irf_ports module to create IRF port
      to physical port bindings, and set activate=true to activate the
      IRF. If IRF neighbors are already configured, the IRF will be
      formed, some devices may reboot.
    - Any physical interfaces not in an interface list (irf_p1 or irf_p2) will
      be removed from the IRF port. An empty list removes all interfaces.
    - If an IRF is successfully created, the non-master members will no longer
      be accessible through their management interfaces.
options:
    member_id:
        description:
            - IRF member id for switch (must be unique).
              IRF member ids can be configured with the comware_irf_members module.
        required: true
        type: str
    irf_p1:
        description:
            - Physical Interface or List of Physical Interfaces that will be
              bound to IRF port 1. Any physical interfaces not in the list will
              be removed from the IRF port. An empty list removes all interfaces.
        required: true
        type: list
        elements: str
    irf_p2:
        description:
            - Physical Interface or List of Physical Interfaces that will be
              bound to IRF port 2. Any physical interfaces not in the list will
              be removed from the IRF port. An empty list removes all interfaces.
        required: true
        type: list
        elements: str
    filename:
        description:
            - Where to save the current configuration. Default is startup.cfg.
        required: false
        default: startup.cfg
        type: str
    activate:
        description:
            - activate the IRF after the configuration is initially performed
        required: false
        default: true
        type: bool
    removal_override:
        description:
            - When set to true, allows the removal of physical ports from IRF port(s).
              Removing physical ports may have adverse effects and be disallowed by the switch.
              Disconnecting all IRF ports could lead to a split-brain scenario.
        required: false
        default: false
        type: bool
"""

EXAMPLES = """

- name: irf ports
  h3c_open.comware.comware_irf_ports:
    member_id: 1
    irf_p1: GigabitEthernet1/0/3
    irf_p2: GigabitEthernet1/0/5
    removal_override: yes

- name: irf ports
  h3c_open.comware.comware_irf_ports:
    member_id: 1
    irf_p1:
      - GigabitEthernet1/0/25
      - GigabitEthernet1/0/30
    irf_p2: GigabitEthernet1/0/26
    removal_override: yes
    activate: false
  tags: '1'

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (get_device)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.irf import (
    IrfMember, IrfPort)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import (
    Interface)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import (
    PYCW7Error, NCTimeoutError, ConnectionClosedError)


def convert_iface_list(device, iface_list):
    converted_list = []
    for iface_name in iface_list:
        iface = Interface(device, iface_name)
        converted_list.append(iface.interface_name)

    return converted_list


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            member_id=dict(type='str',
                           required=True),
            irf_p1=dict(required=True, type='list', elements='str'),
            irf_p2=dict(required=True, type='list', elements='str'),
            filename=dict(default='startup.cfg'),
            activate=dict(type='bool',
                          default='true'),
            removal_override=dict(type='bool',
                                  default='false'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('CHECKMODE', 'member_id', 'look_for_keys')

    device = get_device(module)

    member_id = module.params.get('member_id')
    changed = False

    try:
        irf_mem = IrfMember(device)
        irf_mem.get_config(member_id)
    except PYCW7Error as exc:
        module.fail_json(msg=str(exc))
    existing_full = None
    irf_ports = None
    try:
        irf_ports = IrfPort(device)
        existing_full = irf_ports.get_config()
    except PYCW7Error as exc:
        safe_fail(module, msg=str(exc),
                  descr='Error getting current configuration.')

    existing = existing_full.get(member_id, {})

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    irf_p1 = proposed.get('irf_p1')
    if isinstance(irf_p1, str):
        irf_p1 = [irf_p1]

    if not irf_p1:
        irf_p1 = []

    irf_p2 = proposed.get('irf_p2')
    if isinstance(irf_p2, str):
        irf_p2 = [irf_p2]

    if not irf_p2:
        irf_p2 = []

    try:
        irf_p1 = convert_iface_list(device, irf_p1)
        irf_p2 = convert_iface_list(device, irf_p2)
    except PYCW7Error as ie:
        safe_fail(module, msg=str(ie),
                  descr='Error recognizing physical interface.')

    old_p1 = existing.get('irf_p1', [])
    old_p2 = existing.get('irf_p2', [])
    filename = proposed.pop('filename')
    activate = proposed.pop('activate')
    delta = False

    if set(irf_p1) != set(old_p1):
        delta = True

    if set(irf_p2) != set(old_p2):
        delta = True

    removal_list = []
    for item in old_p1:
        if item not in irf_p1:
            removal_list.append(item)

    for item in old_p2:
        if item not in irf_p2:
            removal_list.append(item)

    removal_override = proposed.get('removal_override')

    if removal_list and not removal_override:
        safe_fail(module, msg='You are trying to remove interfaces ' +
                              '{0}\n'.format(removal_list) +
                              'Removal may have adverse effects.\n' +
                              'Set removal_override=true to override.')

    if delta:
        try:
            irf_ports.build(member_id,
                            old_p1=old_p1,
                            old_p2=old_p2,
                            irf_p1=irf_p1,
                            irf_p2=irf_p2,
                            filename=filename,
                            activate=activate)
        except PYCW7Error as exc:
            safe_fail(module, msg=str(exc),
                      descr='Error preparing IRF port config.')

    commands = None
    end_state = existing

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = end_state

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = irf_ports.get_config()
                changed = True
                results['changed'] = changed
                results['end_state'] = end_state
            except PYCW7Error as exc:
                if isinstance(exc, NCTimeoutError) \
                        or isinstance(exc, ConnectionClosedError):
                    changed = True
                    results['changed'] = changed
                    module.exit_json(**results)
                else:
                    safe_fail(module, msg=str(exc),
                              descr='Error executing commands.'
                                    + 'Please make sure member id is correct.')

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
