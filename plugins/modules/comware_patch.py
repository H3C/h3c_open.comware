#!/usr/bin/python


DOCUMENTATION = '''
---

module: comware_patch
short_description: Manage patch
description:
    - Manage patch
version_added: 1.0.0
category: System (RW)
author: wangliang
notes:
    - This modules rollback the config to startup.cfg, or the supplied
      filename, in flash. It is not
      changing the config file to load on next boot.
options:
    patchname:
        description:
            - Name of patch that will be used .
        required: false
        type: str
    activate:
        description:
            - active patch or not.
        required: false
        default: false
        type: bool
    check_result:
        description: check patch active success or not .
        required: false
        default: false
        type: bool

'''
EXAMPLES = '''

        - name: copy version from ansible server into switch.
          h3c_open.comware.comware_file_copy:
            file: /tmp/s5570s_ei-cmw710-system-patch-r1120.bin
            remote_path: flash:/s5570s_ei-cmw710-system-patch-r1120.bin
            username: "{{ ansible_user }}"
            password: "{{ ansible_password }}"
            hostname: "{{ ansible_host }}"

        - name: check bin is exit or not and active it.
          h3c_open.comware.comware_patch:
            patchname: s5570s_ei-cmw710-system-patch-r1120.bin
            activate: true

        - name: check patch is active or not
          h3c_open.comware.comware_patch:
            patchname: s5570s_ei-cmw710-system-patch-r1120.bin
            check_result: true

'''

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.patch import Patch


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            patchname=dict(required=True),
            activate=dict(required=False, choices=['true', 'false']),
            check_result=dict(required=False, choices=['true', 'false']),
        ),
        supports_check_mode=True
    )

    patchname = module.params['patchname']
    activate = module.params['activate']
    check_result = module.params['check_result']

    args = dict(patchname=patchname, activate=activate, check_result=check_result)

    device = get_device(module)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    changed = False
    commands = []

    check_file = Patch(device, patchname)

    check = check_file.get_file_lists()

    if not check:
        module.fail_json(msg='file {0} not in the flash,please check the name of the patch file'.format(patchname))

    if activate == 'true':
        active = check_file.build(stage=True)
        if not active:
            module.fail_json(msg='activate fail!')

    if check_result == 'true':
        # time.sleep(40)
        result = check_file.Check_result()
        if not result:
            module.fail_json(msg='activate failed!')

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='error during execution')
            changed = True

    results = {'commands': commands, 'changed': changed, 'proposed': proposed}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
