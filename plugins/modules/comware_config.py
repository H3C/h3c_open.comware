#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = '''

---

module: comware_config
short_description: Back uo current configuration to the specified file
description:
    - Back uo current configuration to the specified file
version_added: 1.0.0
author: liudongxue(@liudongxue)
notes:
    - This modules backup the config to specified file in specified flash.
    - You can use the specified file for configuration distribution.
options:
    filefolder:
        description:
            - Full specified backup path on Comware v7 device, e.g. flash:/mypath/.
        required: false
        default:
        type: str
    arcstate:
        description:
            - The switch of backup
        required: false
        default: absent
        choices: ['absent', 'present']
        type: str
    filename:
        description:
            - Backup file
        required: false
        default: my_file
        type: str
    replacefile:
        description:
            - Rolling file
        required: false
        type: str
    repswitch:
        description:
            - Configure rollback switch
        required: false
        type: bool
    y_or_no:
        description:
            - Configure the switch to save the current configuration during rollback.
        required: false
        choices: ['y', 'n']
        type: str

'''
EXAMPLES = '''

  - name: backup config to flash:/llld/ans.cfg (in flash)
    h3c_open.comware.comware_config:
      filename: ans
      arcstate: present
      filefolder: 'flash:/llld/'
    register: results

  - name: rollback config to netconf.cfg and save the current configuration(in flash)
    h3c_open.comware.comware_config:
      repswitch: true
      replacefile: netconf.cfg
      y_or_no: y
    register: results

  - name: rollback config to netconf.cfg and do not save the current configuration
    h3c_open.comware.comware_config:
      repswitch: true
      replacefile: netconf.cfg
      y_or_no: n
    register: results

'''
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file import File
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file_copy import FileCopy


def view_backup_profile(profilelist, file_name):
    c = []
    for v in profilelist:
        if file_name in v:
            c.append(v)
    return c


def config_replace_file(replace_file_list):
    listnum = len(replace_file_list)
    listnum = listnum - 1
    return replace_file_list[listnum]


def filefolder(file_folder):
    remote_dir = ''
    if file_folder.find(':/') < 0 and file_folder != '':
        remote_dir = 'flash:/'
    elif file_folder.find(':/') > 0:
        remote_dir = file_folder.split(':/')[0] + ':/'
    return remote_dir


def check_file_existing(file_lists, tname):
    for each in file_lists:
        each_filename = each.split(':/')[1].strip()
        if each_filename == tname:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filefolder=dict(required=False, type='str'),
            arcstate=dict(required=False, default='absent', choices=['absent', 'present'], type='str'),
            filename=dict(required=False, default='my_file', type='str'),
            replacefile=dict(required=False, type='str'),
            repswitch=dict(required=False, type='bool'),
            y_or_no=dict(required=False, choices=['y', 'n'], type='str'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    filefolder = module.params['filefolder']
    arcstate = module.params['arcstate']
    filename = module.params['filename']
    repswitch = module.params['repswitch']
    replacefile = module.params['replacefile']
    y_or_no = module.params['y_or_no']
    changed = False
    commands = None

    file_copy = FileCopy(device, '', filefolder)
    if not file_copy.remote_dir_exists:
        file_copy.create_remote_dir()
        filefolder = filefolder.strip('/')

    falsh_space = file_copy._get_flash_size()

    rollback_file = File(device, '')
    f_lists = rollback_file.get_rollback_file_lists()
    is_exist = False
    if replacefile:
        if replacefile[-4:] != '.cfg':
            module.fail_json(msg='filename should end with .cfg')
        is_exist = check_file_existing(f_lists, replacefile)
        if not is_exist:
            module.fail_json(msg='Rollback file does not exist')

    if falsh_space < 1000:
        module.fail_json(msg='Not enough flash space')
    if filename:
        if filename[-4:] == '.cfg':
            filename = filename.split('.cfg')[0].strip()
    if arcstate == 'present':
        cmdmand = ['archive configuration location' + ' ' + filefolder + ' ' + 'filename-prefix' + ' ' + filename]
        device.stage_config(cmdmand, 'cli_config')
        cmdmand_1 = []
        cmds = 'archive configuration'
        cmdmand_1.append(cmds)
        cmdmand_1.append('y')
        device.stage_config(cmdmand_1, "cli_display")
    if filefolder == 'flash:/' and arcstate == 'present' and repswitch == 'true':
        cmdmand = ['archive configuration location' + ' ' + filefolder + ' ' + 'filename-prefix' + ' ' + filename]
        device.stage_config(cmdmand, 'cli_config')
        cmdmand_1 = []
        cmds = 'archive configuration'
        cmdmand_1.append(cmds)
        cmdmand_1.append('y')
        device.stage_config(cmdmand_1, "cli_display")
        if view_backup_profile(f_lists, filename) and not replacefile:
            replacefilelist = view_backup_profile(f_lists, filename)
            if repswitch == 'true':
                refile = config_replace_file(replacefilelist)
                cmdmand = ['configuration replace file' + ' ' + filefolder + refile]
                if y_or_no == 'y':
                    cmdmand.append('y')
                    cmdmand.append('y')
                else:
                    cmdmand.append('n')
                device.stage_config(cmdmand, 'cli_config')
    if is_exist:
        if repswitch == 'true':
            cmdmand = ['configuration replace file flash:/' + replacefile]
            if y_or_no == 'y':
                cmdmand.append('y')
                cmdmand.append('y')
            else:
                cmdmand.append('n')
            device.stage_config(cmdmand, 'cli_config')
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
