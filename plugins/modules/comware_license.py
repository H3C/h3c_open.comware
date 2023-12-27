#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_license
short_description: loading device license
description:
    - loading device license
version_added: 1.0.0
category: Feature (RW)
author: null
notes:
    - 
options:
    license:
        description:
            - the license file for the device
        required: True
        type: str
    slot:
        description:
            - device slot number which the license loading.
        required: false
        type: str
    license_chk:
        description:
            - check the license 
        required: false
        default: true
        type: bool
    state:
        description:
            - Desired state for the configuration
        required: false
        default: present
        choices: ['present', 'default']
        type: str
"""
EXAMPLES = """

- name: License activate
  h3c_open.comware.comware_license:
    license: H3CVS7002023122010560173160.ak
    license_chk: false
    slot: 1

- name: License activate check
  h3c_open.comware.comware_license:
    license: H3CVS7002023122010560173160.ak
    license_chk: true
    slot : 1
  register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.license import License


def main():
    module = AnsibleModule(
        argument_spec=dict(
            license=dict(required=True, type='str'),
            slot=dict(type='str'),
            license_chk=dict(default=True, type='bool'),
            state=dict(choices=['present', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    license = module.params.get('license')
    license_chk = module.params.get('license_chk')
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if not module.params.get('slot'):
        module.fail_json(msg='please assign slot number for loading license file')

    licenses = None
    existing = None
    try:
        licenses = License(device, )
    except PYCW7Error as e:
        module.fail_json(descr='there is problem in setting the device license',
                         msg=str(e))
    try:
        existing = licenses.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting existing config.')

    if state == 'present':
        if not existing:
            licenses.build(stage=True, **proposed)
        else:
            license_file = existing.get('license').split('/license/')[1]
            license_state = existing.get('license_state')
            if license_file == license and license_state == 'in use':
                pass
            else:
                licenses.build(stage=True, **proposed)
        if license_chk == 'true':
            current_license = licenses.get_config()
            if not current_license:
                module.fail_json(msg='Invalid activation license file.')
            if current_license.get('license').split('/license/')[1] != license or \
                    current_license.get('license_state').lower() != 'in use':
                module.fail_json(msg='license is invalid')
    # elif state == 'default':
    #     licenses.default(stage=True, **proposed)

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
                end_state = licenses.get_config()
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
