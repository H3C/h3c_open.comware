#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_install_config
short_description: Activate a new current-running config in realtime
description:
    - Activate a new current-running config in realtime
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - Check mode copies config file to device and still generates diffs
    - diff_file must be specified to write diffs to a file, otherwise,
      only summarized diffs are returned from the module
    - commit_changes must be true to apply changes
    - this module does an automatic backup of the existing config
      to the filename flash:/safety_file.cfg
    - this module does an auto save to flash:/startup.cfg upon completion
    - config_file MUST be a valid FULL config file for a given device.
options:
    config_file:
        description:
            - File that will be sent to the device.  Relative path is
              location of Ansible playbook.  Recommended to use
              absolute path.
        required: true
        type: str
    commit_changes:
        description:
            - Used to determine the action to take after transferring the
              config to the switch.  Either activate using the rollback
              feature or load on next-reboot.
        required: true
        type: bool
    diff_file:
        description:
            - File that will be used to store the diffs.  Relative path is
              location of ansible playbook. If not set, no diffs are saved.
        required: false
        type: str
    hostname:
        description:
            - IP Address or hostname of the Comware 7 device that has
              NETCONF enabled
        required: true
        type: str
    username:
        description:
            - Username used to login to the switch
        required: true
        type: str
    password:
        description:
            - Password used to login to the switch
        required: false
        type: str
    look_for_keys:
        description:
            - Whether searching for discoverable private key files in ~/.ssh/
        required: false
        default: False
        type: bool

"""
EXAMPLES = """

# install config file that will be the new running config
- comware_install_config:
    config_file='/root/ansible_collections.h3c_open.comware.plugins.module_utils.network.comware-ansible-master/gqy/123.cfg'
    diff_file='/root/ansible_collections.h3c_open.comware.plugins.module_utils.network.comware-ansible-master/gqy/diffs.diff'
    commit_changes=true
    username={{ username }}
    password={{ password }}
    hostname={{ inventory_hostname }}

"""
import os

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error, NCError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.config import Config
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file_copy import FileCopy


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
            config_file=dict(required=True, type='str'),
            diff_file=dict(required=False, type='str'),
            commit_changes=dict(required=True, type='bool'),
            hostname=dict(required=True),
            username=dict(required=True),
            password=dict(required=False, default=None, no_log=True),
            look_for_keys=dict(default=False, type='bool'),
        ),
        supports_check_mode=True
    )

    username = module.params['username']
    password = module.params['password']
    hostname = module.params['hostname']
    look_for_keys = module.params['look_for_keys']

    device = get_device(module)
    config_file = module.params['config_file']
    diff_file = module.params['diff_file']
    commit_changes = module.params['commit_changes']

    changed = False
    file_exists = False

    if os.path.isfile(config_file):
        file_exists = True
    else:
        module.fail_json(msg='Cannot find/access config_file:\n{0}'.format(
            config_file))
    cfg = None
    basename = None
    if file_exists:
        basename = os.path.basename(config_file)
        try:
            copy = FileCopy(device,
                            src=config_file,
                            dst='flash:/{0}'.format(basename))
            copy.transfer_file(hostname,
                               username,
                               password,
                               look_for_keys)
            cfg = Config(device, config_file)
        except PYCW7Error as fe:
            module.fail_json(msg=str(fe),
                             descr='file transfer error')

    if diff_file:
        diffs, full_diffs = cfg.compare_config()
        write_diffs(diff_file, diffs, full_diffs)
    else:
        diffs = 'None.  diff_file param not set in playbook'

    cfg.build(stage=True)

    active_files = {}
    if device.staged:
        active_files = dict(backup='flash:/safety_file.cfg',
                            startup='flash:/startup.cfg',
                            config_applied='flash:/' + basename)
        if module.check_mode:
            module.exit_json(changed=True,
                             active_files=active_files,
                             diffs=diffs,
                             diff_file=diff_file,
                             config_file=config_file)
        else:
            if commit_changes:
                try:
                    device.execute_staged()
                except NCError as err:
                    if err.tag == 'operation-failed':
                        module.fail_json(msg='Config replace operation'
                                             + ' failed.\nValidate the config'
                                             + ' file being applied.')
                except PYCW7Error as e:
                    module.fail_json(msg=str(e),
                                     descr='error during execution')

                changed = True

    results = {}
    results['changed'] = changed
    results['active_files'] = active_files
    results['commit_changes'] = commit_changes
    results['diff_file'] = diff_file
    results['config_file'] = config_file

    module.exit_json(**results)


if __name__ == "__main__":
    main()
