#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_dldp
short_description: Manage dldp authentication,interface,timeout and mode  on Comware 7 devices.
description:
    - Manage dldp authentication,interface,timeout and mode  on Comware 7 devices.
author: gongqianyu(@gongqianyu)
version_added: 1.0.0
notes:
    - To enable the dldp feature, the dldp feature must be enabled on both the global and the interface.
    - when config interface_enable,init_delay and port_shutdown,name must be exit.
options:
    global_enable:
        description:
            - Global dldp enable or disable
        required: False
        choices: [enable, disable]
        type: str
    auth_mode:
        description:
            - Configure dldp authentication mode between current device and neighbor device.
        required: false
        choices: [md5, none, simple]
        type: str
    pwd_mode:
        description:
            - Configure the dldp authentication password mode between the current device and the neighbor device.
        required: false
        choices: [cipher, simple]
        type: str
    pwd:
        description:
            - Configure the dldp authentication password between the current device and the neighbor device
        required: false
        type: str

    timeout:
        description:
            - Configure the sending interval of advertisement message(1~100)
        required: false
        default: 5
        type: int
    shutdown_mode:
        description:
            - Global configuration of interface shutdown mode after dldp discovers unidirectional link.
        required: false
        choices: [auto, hybrid, manual]
        type: str
    name:
        description:
            - The full name of the interface.
        required: false
        type: str
    interface_enable:
        description:
            - Enable dldp function on the interface.
        required: false
        choices: [enable, disable]
        type: str
    init_delay:
        description:
            - Delay time of dldp blocking interface from initial state to single pass state.(1~5)
        required: false
        type: str

    port_shutdown:
        description:
            - The interface shutdown mode after dldp discovers one-way link is configured on the interface.
        required: false
        choices: [auto, hybrid, manual]
        type: str
    state:
        description:
            - Desired state for the interface configuration.
        required: false
        default: present
        choices: ['present', 'absent']
        type: str

"""

EXAMPLES = """

- name: Config dldp
  h3c_open.comware.comware_dldp:
    global_enable: enable
    auth_mode: md5
    shutdown_mode: auto
    pwd_mode: cipher
    pwd: 123456
    timeout: 10
    name: HundredGigE1/0/27
    interface_enable: disable
    state: present
  register: results

- name: Delete dldp configuration
  h3c_open.comware.comware_dldp:
    global_enable: enable
    auth_mode: md5
    shutdown_mode: auto
    pwd_mode: cipher
    pwd: 123456
    timeout: 10
    name: HundredGigE1/0/27
    interface_enable: disable
    state: absent
  register: results

- name: Config dldp
  h3c_open.comware.comware_dldp:
    global_enable: disable
    auth_mode: simple
    shutdown_mode: manual
    pwd_mode: simple
    pwd: 123456
    timeout: 20
    name: HundredGigE1/0/25
    interface_enable: enable
    port_shutdown: manual
    state: present
  register: results

- name: Delete dldp
  h3c_open.comware.comware_dldp:
    name: HundredGigE1/0/25
    state: absent
  register: results

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.dldp import Dldp


def main():
    module = AnsibleModule(
        argument_spec=dict(
            global_enable=dict(required=False, choices=['enable', 'disable'], type='str'),
            auth_mode=dict(required=False, choices=['md5', 'none', 'simple'], type='str'),
            pwd_mode=dict(required=False, choices=['cipher', 'simple'], type='str'),
            pwd=dict(required=False, type='str'),
            timeout=dict(required=False, default='5', type='int'),
            name=dict(required=False, type='str'),
            interface_enable=dict(required=False, choices=['enable', 'disable'], type='str'),
            init_delay=dict(required=False, type='str'),
            shutdown_mode=dict(required=False, choices=['auto', 'hybrid', 'manual'], type='str'),
            port_shutdown=dict(required=False, choices=['auto', 'hybrid', 'manual'], type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    global_enable = module.params['global_enable']
    auth_mode = module.params['auth_mode']
    pwd_mode = module.params['pwd_mode']
    pwd = module.params['pwd']
    timeout = module.params['timeout']
    name = module.params['name']
    interface_enable = module.params['interface_enable']
    init_delay = module.params['init_delay']
    shutdown_mode = module.params['shutdown_mode']
    port_shutdown = module.params['port_shutdown']
    state = module.params['state']
    args = dict(global_enable=global_enable, auth_mode=auth_mode, port_shutdown=port_shutdown, timeout=timeout,
                pwd_mode=pwd_mode, init_delay=init_delay, pwd=pwd, name=name, interface_enable=interface_enable,
                shutdown_mode=shutdown_mode)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    changed = False
    DLDP = None

    try:
        DLDP = Dldp(device,
                    global_enable,
                    auth_mode,
                    timeout,
                    port_shutdown,
                    pwd_mode,
                    init_delay,
                    pwd,
                    name,
                    interface_enable,
                    shutdown_mode)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    if state == 'present':
        DLDP.build(stage=True)
    elif state == 'absent':
        DLDP.remove(stage=True)

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
