#!/usr/bin/python


DOCUMENTATION = '''
---

module: comware_rollback
short_description: Rollback the running configuration
description:
    - Rollback theconfiguration to the file
version_added: 1.0.0
category: System (RW)
author: wangliang
notes:
    - This modules rollback the config to startup.cfg, or the supplied
      filename, in flash. It is not
      changing the config file to load on next boot.
options:
    filename:
        description:
            - Name of file that will be used when rollback the conifg to flash.
        required: false
        default: startup.cfg
        type: str
    comparefile:
        description:
            - Name of file that will be used when compared with filename file. 
              if not set, no compared action executed.
        required: false
        type: str
    clean:
        description:
            - delete the rollback point
        required: false
        default: false
        type: bool
    diff_file:
        description:
            - File that will be used to store the diffs.  Relative path is
              location of ansible playbook. If not set, no diffs are saved.
        required: false
        type: str

'''
EXAMPLES = '''

  - name: Rollback config to myfile.cfg (in flash)
    h3c_open.comware.comware_rollback:
      filename: netconf.cfg
    register: results

  - name: Rollback config to startup.cfg (in flash)
    h3c_open.comware.comware_rollback:
    register: results

  - name: Delete rollback point 123.cfg (in flash)
    h3c_open.comware.comware_rollback:
      filename: 123.cfg
      clean: true
    register: results

  - name: Files compared
    h3c_open.comware.comware_rollback:
      filename: 1.cfg
      comparefile: netconf.cfg
      diff_file: '../diffs.diff'
    register: results
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file import File


def check_file_existing(file_lists, tname):
    for each in file_lists:
        each_filename = each.split(':/')[1].strip()
        if each_filename == tname:
            return True
    return False


def write_diffs(diff_file, diffs, full_diffs):

    with open(diff_file, 'w+') as diff:
        diff.write("#######################################\n")
        diff.write('########## SUMMARY OF DIFFS ###########\n')
        diff.write("#######################################\n")
        diff.write('\n\n')
        diff.write('\n'.join(diffs))
        diff.write('\n\n\n')
        diff.write("#######################################\n")
        diff.write('FULL DIFFS AS RETURNED BACK FROM SWITCH\n')
        diff.write("#######################################\n")
        diff.write('\n\n')
        diff.write('\n'.join(full_diffs))
        diff.write('\n')


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filename=dict(required=False, default='startup.cfg', type='str'),
            clean=dict(required=False, default='false', choices=['true', 'false']),
            diff_file=dict(required=False, type='str'),
            comparefile=dict(required=False, default=None, type='str'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    filename = module.params['filename']
    comparefile = module.params['comparefile']
    diff_file = module.params['diff_file']
    clean = module.params['clean']
    if "/" in filename:
        module.fail_json(msg="specify only filename")
    if filename[-4:] != '.cfg':
        module.fail_json(msg='filename should end with .cfg')

    changed = False
    commands = ''

    rollback_file = File(device, filename, comparefile)
    f_lists = rollback_file.get_rollback_file_lists()
    if not check_file_existing(f_lists, filename):
        module.fail_json(msg='file {0} not in the flash,please check the name of the rollback file'.format(filename))

    if comparefile and diff_file:
        if "/" in comparefile:
            module.fail_json(msg="specify only comparefile")
        if filename[-4:] != '.cfg':
            module.fail_json(msg='comparefile should end with .cfg')
        if not check_file_existing(f_lists, comparefile):
            module.fail_json(
                msg='file {0} not in the flash,please check the name of the rollback file'.format(comparefile))

        diffs, full_diffs = rollback_file.compare_rollback_files()
        write_diffs(diff_file, diffs, full_diffs)

    else:
        diffs = 'None.  diff_file param not set in playbook'

    if clean == 'false':
        device.stage_config('{0}'.format(filename), "rollback")
    elif clean == 'true':
        cmdmand = []
        cmd = 'delete /unreserved flash:/{0}'.format(filename)
        cmdmand.append(cmd)
        cmdmand.append('y')
        device.stage_config(cmdmand, "cli_display")

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
    results['commands'] = commands
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
