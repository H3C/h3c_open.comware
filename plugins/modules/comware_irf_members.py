#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_irf_members
short_description: Manage IRF membership configuration
description:
    - Manage IRF member configuration.
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - This module should be used before the comware_irf_ports module.
    - The process is as follows 1) Use comware_irf_members to change
      the IRF member identity of the device, with the reboot=true
      flag, or reboot the device through some other means. 2) Use
      comware_irf_members to change priority, description, and domain,
      if desired. 3) Use the comware_irf_ports module to create IRF port
      to physical port bindings, and set activate=true to activate the
      IRF. If IRF neighbors are already configured, the IRF will be
      formed, some devices may reboot.
    - When state=absent, the interfaces in mad_exclude will be removed if present.
      Other parameters will be ignored.
options:
    member_id:
        description:
            - Current IRF member ID of the switch.
              If the switch has not been configured for IRF yet,
              this should be 1.
        required: true
        type: str
    new_member_id:
        description:
            - The desired IRF member ID for the switch.
              The new member ID takes effect after a reboot.
        required: false
        type: str
    auto_update:
        description:
            - Whether software autoupdate should be enabled for the fabric.
        required: false
        choices: ['enable', 'disable']
        type: str
    domain_id:
        description:
            - The domain ID for the IRF fabric.
        required: false
        type: str
    mad_exclude:
        description:
            - Interface or list of interfaces
              that should be excluded from shutting down
              in a recovery event.
        required: false
        type: str
    priority:
        description:
            - The desired IRF priority for the switch.
        required: false
        type: str
    descr:
        description:
            - The text description of the IRF member switch.
        required: false
        type: str
    reboot:
        description:
            - Whether to reboot the switch after member id changes are made.
        required: true
        type: bool
    state:
        description:
            - Desired state of the interfaces listed in mad_exclude
        required: false
        default: 'present'
        choices: ['present', 'absent']
        type: str

"""

EXAMPLES = """

  # irf members
  - comware_irf_members:
      member_id: 9
      state: present
      auto_update: disable
      mad_exclude:
        - FortyGigE9/0/30
        - FortyGigE9/0/23
        - FortyGigE9/0/24
      priority: 4
      descr: My description
      reboot: no

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.irf import IrfMember
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.reboot import Reboot
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import \
    IRFMemberDoesntExistError, InterfaceError
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
            new_member_id=dict(type='str'),
            auto_update=dict(choices=['enable', 'disable'], type='str'),
            domain_id=dict(type='str'),
            mad_exclude=dict(type='str'),
            priority=dict(type='str'),
            descr=dict(type='str'),
            reboot=dict(type='bool',
                        required=True),
            state=dict(choices=['present', 'absent'],
                       default='present',
                       type='str'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('CHECKMODE', 'look_for_keys')

    device = get_device(module)

    member_id = module.params.pop('member_id')
    reboot = module.params.pop('reboot')
    state = module.params.get('state')

    changed = False

    existing = None
    irfm = None
    try:
        irfm = IrfMember(device)
        existing = irfm.get_config(member_id)
    except PYCW7Error as exe:
        if isinstance(exe, IRFMemberDoesntExistError):
            new_member_id = module.params.get('new_member_id')
            try:
                if new_member_id:
                    member_id = new_member_id
                    irfm = IrfMember(device)
                    existing = irfm.get_config(member_id)
                else:
                    safe_fail(module, msg=str(exe))
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe))
        else:
            safe_fail(module, msg=str(exe))

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    mad_exclude = proposed.pop('mad_exclude', [])
    if isinstance(mad_exclude, str):
        mad_exclude = [mad_exclude]

    if mad_exclude:
        try:
            mad_exclude = convert_iface_list(device, mad_exclude)
        except InterfaceError as ie:
            module.fail_json(msg=str(ie))

    existing_mad_exclude = existing.pop('mad_exclude', [])
    mad_delta = list(set(mad_exclude).difference(
        existing_mad_exclude))

    delta = dict(set(proposed.items()).difference(
        existing.items()))

    proposed['mad_exclude'] = mad_exclude
    existing['mad_exclude'] = existing_mad_exclude

    if state == 'present':
        if delta or mad_delta:
            try:
                irfm.build(
                    stage=True,
                    member_id=member_id, mad_exclude=mad_delta, **delta)
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='There was an error preparing the'
                                + ' IRF membership configuration.')
    elif state == 'absent':
        remove_mad = list(set(mad_exclude).intersection(
            existing_mad_exclude))
        irfm.remove_mad_exclude(remove_mad)

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
                end_state = irfm.get_config(member_id)
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe))
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'commands': commands, 'changed': changed,
               'end_state': end_state, 'state': state}

    new_member_id = proposed.get('new_member_id')
    mem_id_changed = False
    if new_member_id:
        mem_id_changed = proposed.get('new_member_id') != member_id

    if reboot and mem_id_changed:
        try:
            my_reboot = Reboot(device)
            my_reboot.build(reboot=True)
            device.execute()
        except PYCW7Error as exe:
            if isinstance(exe, NCTimeoutError) \
                    or isinstance(exe, ConnectionClosedError):
                module.exit_json(**results)
            else:
                safe_fail(module, msg=str(exe))

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
