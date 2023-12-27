#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_interface
short_description: Manage administrative state and physical attributes of the interface
description:
    - Manage administrative state and physical attributes of the interface
version_added: 1.0.0
category: Feature (RW)
author: liudongxue
notes:
    - Only logical interfaces can be removed with state=absent.
    - If you want to configure type (bridged or routed),
      run this module first with no other interface parameters.
      Then, remove the type parameter and include the other desired parameters.
      When the type parameter is given, other parameters are defaulted.
    - When state is set to default, the interface will be "defaulted"
      regardless of what other parameters are entered.
    - When state is set to default, the interface must already exist.
    - When state is set to absent, logical interfaces will be removed
      from the switch, while physical interfaces will be "defaulted"
    - Tunnel interface creation and removal is not currently supported.
options:
    name:
        description:
            - Full name of the interface
        required: true
        type: str
    admin:
        description:
            - Admin state of the interface
        required: false
        default: up
        type: str
    description:
        description:
            - Single line description for the interface
        required: false
        type: str
    type:
        description:
            - Type of interface, i.e. L2 or L3
        required: false
        type: str
    duplex:
        description:
            - Duplex of the interface
        required: false
        type: str
    speed:
        description:
            - Speed of the interface in Mbps
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        type: str

"""
EXAMPLES = """

  - name: 'Basic Ethernet alternate parameters'
    h3c_open.comware.comware_interface:
      name: HundredGigE1/0/25
      admin: down
      description: newdesc
      duplex: full
      speed: auto

  - name: 'Basic Ethernet idempotency'
    h3c_open.comware.comware_interface:
      name: HundredGigE1/0/25
      admin: up
      description: mydesc
      duplex: auto
      speed: 40000

"""

import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import InterfaceError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            admin=dict(choices=['up', 'down']),
            description=dict(),
            type=dict(choices=['bridged', 'routed']),
            duplex=dict(choices=['auto', 'full']),
            speed=dict(type='str'),
            state=dict(choices=['present', 'absent', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'name')

    device = get_device(module)

    name = module.params['name']
    subnum_list = name.split('.')
    state = module.params['state']
    changed = False

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)
    interface = None
    try:
        interface = Interface(device, name)
    except PYCW7Error as exc:
        module.fail_json(descr='There was problem recognizing that interface.',
                         msg=str(exc))

    try:
        interface.param_check(**proposed)
    except PYCW7Error as exc:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(exc))

    existing = {}
    try:
        existing = interface.get_config()
    except PYCW7Error as exc:
        module.fail_json(msg=str(exc),
                         descr='Error getting existing config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta or not existing:
            if not interface.iface_exists:
                try:
                    interface.create_logical()
                    interface.update()
                    changed = True
                    existing = interface.get_config()
                except PYCW7Error as exc:
                    module.fail_json(msg='Exception message ' + str(exc),
                                     descr='There was a problem creating'
                                           + ' the logical interface.')

                delta = dict(set(proposed.items()).difference(
                    existing.items()))

            if delta:
                res_sub = re.search(r'\.', name)
                if interface.is_routed and res_sub is not None:
                    interface.create_sub_iface(stage=True)
                interface.build(stage=True, **delta)
        else:
            res_sub = re.search(r'\.', name)
            if interface.is_routed and res_sub is not None:
                interface.create_sub_iface(stage=True)

    elif state == 'default':
        defaults = interface.get_default_config()
        delta = dict(set(existing.items()).difference(
            defaults.items()))
        if delta:
            interface.default(stage=True)
    elif state == 'absent':
        if interface.iface_exists:
            if interface.is_logical_iface():
                try:
                    interface.remove_logical(stage=True)
                except InterfaceError as exc:
                    module.fail_json(msg=str(exc),
                                     descr='Error removing logical interface.')
            elif interface.is_ethernet:
                defaults = interface.get_default_config()
                delta = dict(set(existing.items()).difference(
                    defaults.items()))
                if delta:
                    try:
                        interface.default(stage=True)
                    except InterfaceError as exc:
                        module.fail_json(msg=str(exc),
                                         descr='Error getting default configuration.')
            elif len(subnum_list) == 2:
                try:
                    interface.remove_sub_iface(stage=True)
                except InterfaceError as exc:
                    module.fail_json(msg=str(exc),
                                     descr='Error removing routing sub interface.')

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
                end_state = interface.get_config()
            except PYCW7Error as exc:
                module.fail_json(msg=str(exc),
                                 descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    module.exit_json(**results)


if __name__ == "__main__":
    main()
