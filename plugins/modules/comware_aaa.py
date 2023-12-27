#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_aaa
short_description: This module provides AAA related management configuration and applications
description:
    - This module provides AAA related management configuration and applications
version_added: 1.0.0
category: Feature (RW)
author: null
notes: 
    - When the state is present, all options are required.
    - This module support access type include 'LANaccess','login','super','PPP','default','portal',
       other types to be updated.
    -  Scheme list include 'HWTACACS','RADIUS','local' are permitted. 
    -  If the aaa_type is authentication , access_type can't be super.
    -  If the access_type is super , scheme_list not support for local.

options:
    domain_name:
        description:
            - Configure SSL VPN access instance to use the specified ISP domain for AAA Authentication
        required: true
        type: str
    aaa_type:
        description:
            - Safety certification method.
        required: false
        type: str
    access_type:
        description:
            - Configure authorization methods for LAN access users.
        required: false
        type: str
    scheme_list:
        description:
            - AAA method types
        required: false
        type: str
    scheme_name_list:
        description:
            - Scheme name list.
        required: false
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        type: str
    
"""
EXAMPLES = """

# Basic Ethernet config
    - name: create domain myserver and config it
      h3c_open.comware.comware_aaa:
        domain_na me: myserver
        aaa_type: authentication
        access_type: default
        scheme_list: radius
        scheme_name_list: test

    - name: delete domain name myserver relates
      h3c_open.comware.comware_aaa:
        domain_name: myserver
        state: default
"""

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.aaa import Aaa
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            domain_name=dict(required=True),
            aaa_type=dict(choices=['authentication', 'authorization', 'accounting']),
            access_type=dict(choices=['LANaccess', 'login', 'super', 'PPP',
                                      'default', 'portal']),
            scheme_list=dict(choices=['radius', 'hwtacacs', 'local']),
            scheme_name_list=dict(type='str'),
            state=dict(choices=['present', 'absent', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    domain_name = module.params['domain_name']
    scheme_name = module.params['scheme_name_list']
    access_type = module.params['access_type']
    if state == 'present':
        if module.params['aaa_type'] is not None and module.params['access_type'] is not None and \
                module.params['scheme_list'] is not None and module.params['scheme_name_list'] is not None:
            pass
        else:
            safe_fail(module, msg='All options are required')

    if access_type == 'LANaccess':
        access_type = 'LAN access'
        module.params.update(access_type=access_type)
    if scheme_name:
        if len(scheme_name) < 10:
            scheme_name_list = '0' + str(len(scheme_name)) + scheme_name
        else:
            scheme_name_list = str(len(scheme_name)) + scheme_name
        module.params.update(scheme_name_list=scheme_name_list)
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    aaa = None
    try:
        aaa = Aaa(device, domain_name)
    except PYCW7Error as exe:
        safe_fail(module, descr='there is problem in setting localuser',
                  msg=str(exe))

    try:
        aaa.param_check(**proposed)
    except PYCW7Error as exe:
        safe_fail(module, descr='There was problem with the supplied parameters.',
                  msg=str(exe))

    existing = None
    existing_domain = None
    try:
        existing_domain = aaa.get_domain_info()
        existing = aaa.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting existing config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            delta_domain = dict(domain_name=domain_name)
            aaa.build(stage=True, **delta_domain)
            aaa.build_aaa(stage=True, **proposed)

    elif state == 'default' or 'absent':
        if domain_name in existing_domain:
            delta = dict(domain_name=domain_name)
            aaa.default(stage=True, **delta)

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
                end_state = aaa.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
