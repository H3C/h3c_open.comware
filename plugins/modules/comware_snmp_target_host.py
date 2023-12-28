#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_snmp_target_host
short_description: Manages SNMP user configuration on H3c switches.
description:
    - Manages SNMP target host configuration on H3c switches.
version_added: 1.0.0
author: wangliang (@wangliang)
options:
    target_type:
        description:
            - Notifications type.
        default: trap
        choices: ['inform', 'trap']
        type: str
    usm_user_name:
        description:
            - Unique name for the user.
        required: true
        type: str
    server_address:
        description:
            - Address of the remote manage.
        required: true
        type: str
    vpnname:
        description:
            - VRF instance name.
        required: false
        type: str
    security_model:
        description:
            - The security model by this user is provided.
        required: false
        choices: ['v1', 'v2c', 'v3']
        type: str
    security_level:
        description:
            - The security level by this user is provided.
        required: false
        default: noAuthNoPriv
        choices: ['noAuthNoPriv', 'authentication', 'privacy']
        type: str
    state:
        description:
            - Manage the state of the resource.
        required: false
        default: present
        choices: ['present','absent']
        type: str
"""

EXAMPLES = """
  - name: Config SNMP v3 TargetHost
    h3c_open.comware.comware_snmp_target_host:
      state: present
      target_type: trap
      server_address: 10.1.1.1
      usm_user_name: Uv3
      security_model: v3
      security_level: authentication
      vpnname: testvpn

  - name: Undo SNMP v3 TargetHost
    h3c_open.comware.comware_snmp_target_host:
      state: absent
      target_type: trap
      server_address: 10.1.1.1
      usm_user_name: Uv3
      vpnname: testvpn

  - name: Config SNMP v2c TargetHost
    h3c_open.comware.comware_snmp_target_host:
      state: present
      target_type: trap
      server_address: 100.1.1.1
      usm_user_name: testuv2c
      security_model: v2c

  - name: Undo SNMP v2c TargetHost
    h3c_open.comware.comware_snmp_target_host:
      state: absent
      target_type: trap
      server_address: 100.1.1.1
      usm_user_name: testuv2c
      security_model: v2c
      vpnname: testvpn

  - name: Config SNMP TargetHost
    h3c_open.comware.comware_snmp_target_host:
      state: present
      target_type: inform
      server_address: 100.1.1.1
      usm_user_name: testuv2c
      security_model: v2c

  - name: Undo SNMP TagetHost
    h3c_open.comware.comware_snmp_target_host:
      state: absent
      target_type: inform
      server_address: 100.1.1.1
      usm_user_name: testuv2c
      security_model: v2c
      vpnname: testvpn
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.snmp_target_host import \
    SnmpTargetHost


def param_check_snmp_target_host(**kwargs):
    """Basic param validation for target host

    Args:
        kwargs: params
    """

    module = kwargs["module"]
    usm_user_name = module.params['usm_user_name']
    target_type = module.params['target_type']
    vpnname = module.params['vpnname']
    server_address = module.params['server_address']
    security_model = module.params['security_model']
    security_level = module.params['security_level']

    if usm_user_name and server_address and target_type:
        if security_model != 'v3' and security_level != 'noAuthNoPriv':
            module.fail_json(
                msg='only v3 have authentication and privacy config')

        if len(usm_user_name) > 32 or len(usm_user_name) == 0:
            module.fail_json(
                msg='Error: The len of usm_user_name %s is out of [1 - 32].' % usm_user_name)
        if vpnname:
            if len(vpnname) > 32 or len(vpnname) == 0:
                module.fail_json(
                    msg='Error: The len of vpnname %s is out of [1 - 32].' % vpnname)

    else:
        module.fail_json(
            msg='please provide usm_user_name, target_type and server_address at least')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(choices=['present', 'absent'], default='present'),
            target_type=dict(choices=['inform', 'trap'], default='trap'),
            vpnname=dict(type='str'),
            usm_user_name=dict(required=True, type='str'),
            server_address=dict(required=True, type='str'),
            security_model=dict(choices=['v1', 'v2c', 'v3']),
            security_level=dict(choices=['noAuthNoPriv', 'authentication', 'privacy'], default='noAuthNoPriv'),
        ),
        supports_check_mode=True
    )

    existing = dict()
    changed = False

    filtered_keys = ('hostname', 'username', 'password', 'state',
                     'port', 'look_for_keys')

    state = module.params['state']
    usm_user_name = module.params['usm_user_name']
    target_type = module.params['target_type']
    server_address = module.params['server_address']

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    device = get_device(module)

    snmp_target_host_obj = None
    try:
        snmp_target_host_obj = SnmpTargetHost(device, target_type, server_address, usm_user_name)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem recognizing that server_address.',
                         msg=str(e))

    try:
        param_check_snmp_target_host(module=module)
    except PYCW7Error as e:
        module.fail_json(descr='There was problem with the supplied parameters.',
                         msg=str(e))

    try:
        existing = snmp_target_host_obj.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        snmp_target_host_obj.target_host_build(stage=True, **proposed)
    elif state == 'absent':
        if existing:
            snmp_target_host_obj.target_host_remove(stage=True, **proposed)

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
                end_state = snmp_target_host_obj.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')
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
