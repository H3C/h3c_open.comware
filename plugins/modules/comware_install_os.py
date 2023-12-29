#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_install_os
short_description: Copy (if necessary) and install
    a new operating system on Comware v7 device
description:
    - Offers ability to copy and install a new operating system on Comware v7
      devices.  Supports using .ipe or .bin system and boot packages.
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - The parameters ipe_package and boot/system are
      mutually exclusive.
    - If the files are not currently on the device,
      they will be transfered to the device.
options:
    ipe_package:
        description:
            - File (including abs path path) of the local ipe package.
        required: false
        type: str
    boot:
        description:
            - File (including abs path) of the local boot package (.bin)
        required: false
        type: str
    system:
        description:
            - File (including abs path) of the local system package (.bin)
        required: false
        type: str
    remote_dir:
        description:
            - The remote directory into which the file(s) would be copied.
              See default.
        required: false
        default: flash:/
        type: str
    delete_ipe:
        description:
            - If ipe_package is used,
              this specifies whether the .ipe file is deleted from the device
              after it is unpacked.
        required: false
        default: false
        type: bool
    reboot:
        description:
            - Determine if the reboot should take place
              after device startup software image is configured
        required: true
        type: bool
    delay:
        description:
            - If reboot is set to yes, this is the delay in minutes
              to wait before rebooting.
        required: false
        type: str
    hostname:
        description:
            - IP Address or hostname of the Comware v7 device that has
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

"""
EXAMPLES = """

      - name: Basic Install OS IPE
        h3c_open.comware.comware_install_os:
          ipe_package: /tmp/S5570S_EI-CMW710-R1120.ipe
          reboot: false
          username: "{{ ansible_user }}"
          password: "{{ ansible_password }}"
          hostname: "{{ ansible_host }}"

      - name: Basic Install OS IPE idempotency
        h3c_open.comware.comware_install_os:
          ipe_package: /tmp/S5570S_EI-CMW710-R1120.ipe
          reboot: false
          username: "{{ ansible_user }}"
          password: "{{ ansible_password }}"
          hostname: "{{ ansible_host }}"

"""
import os
import re
import socket

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file_copy import FileCopy
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.install_os import InstallOs
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.reboot import Reboot
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ipe_package=dict(),
            boot=dict(),
            system=dict(),
            remote_dir=dict(default='flash:/'),
            delete_ipe=dict(type='bool',
                            default=False),
            reboot=dict(required=True,
                        type='bool'),
            delay=dict(type='str'),
            hostname=dict(required=True, type='str'),
            username=dict(required=True, type='str'),
            password=dict(required=False, default=None, no_log=True),
        ),
        supports_check_mode=True
    )

    ipe_package = module.params.get('ipe_package')
    boot = module.params.get('boot')
    system = module.params.get('system')
    hostname = socket.gethostbyname(module.params['hostname'])
    username = module.params['username']
    password = module.params['password']

    if ipe_package:
        if boot or system:
            module.fail_json(
                msg='ipe_package and boot/system parameters are mutually exclusive')
    else:
        if not (boot and system):
            module.fail_json(
                msg='boot and system parameters must be provided if ipe_package is not')

    device = get_device(module)
    changed = False

    reboot = module.params.get('reboot')
    delay = module.params.get('delay')
    already_set = False
    transfered = False

    ios = None
    existing = None
    try:
        ios = InstallOs(device)
        existing = ios.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting current config.')

    existing_boot = existing['startup-primary']['boot']
    existing_system = existing['startup-primary']['system']
    remote_dir = module.params['remote_dir']

    if ipe_package:
        ipe_basename = os.path.basename(ipe_package)
        ipe_boot_sys = re.split(r'[-.]', ipe_basename)[-3:-1]
        if ipe_boot_sys:
            if ipe_boot_sys[0].lower() in existing_boot.lower() \
                    and ipe_boot_sys[0].lower() in existing_system.lower() \
                    and ipe_boot_sys[1].lower() in existing_boot.lower() \
                    and ipe_boot_sys[1].lower() in existing_system.lower():
                already_set = True

        ipe_dst = remote_dir + ipe_basename
        ipe_file_copy = None
        try:
            # preps transfer and checks if source file exists
            ipe_file_copy = FileCopy(device, ipe_package, ipe_dst)
        except PYCW7Error as fe:
            safe_fail(module, msg=str(fe),
                      descr='Error preparing IPE file transfer.')

        if not ipe_file_copy.file_already_exists:
            try:
                ipe_file_copy.transfer_file(hostname, username, password)
                transfered = True
            except PYCW7Error as fe:
                safe_fail(module, msg=str(fe),
                          descr='Error transfering IPE file.')

        if not already_set:
            delete_ipe = module.params.get('delete_ipe')
            ios.build(
                'ipe', ipe=ipe_file_copy.dst, delete_ipe=delete_ipe, stage=True)
    elif boot:
        boot_basename = os.path.basename(boot)
        system_basename = os.path.basename(system)
        if boot_basename in existing_boot \
                and system_basename in existing_system:
            already_set = True

        boot_dst = remote_dir + boot_basename
        boot_file_copy = None
        try:
            # preps transfer and checks if source file exists
            boot_file_copy = FileCopy(device, boot, boot_dst)
        except PYCW7Error as fe:
            safe_fail(module, msg=str(fe),
                      descr='Error preparing boot file transfer.')

        system_dst = remote_dir + system_basename
        system_file_copy = None
        try:
            # preps transfer and checks if source file exists
            system_file_copy = FileCopy(device, system, system_dst)
        except PYCW7Error as fe:
            safe_fail(module, msg=str(fe),
                      descr='Error preparing system file transfer.')

        if not boot_file_copy.file_already_exists:
            try:
                boot_file_copy.transfer_file(hostname, username, password)
                transfered = True
            except PYCW7Error as fe:
                safe_fail(module, msg=str(fe),
                          descr='Error transfering boot file.')

        if not system_file_copy.file_already_exists:
            try:
                system_file_copy.transfer_file(hostname, username, password)
                transfered = True
            except PYCW7Error as fe:
                safe_fail(module, msg=str(fe),
                          descr='Error transfering system file.')

        if not already_set:
            ios.build(
                'bootsys', boot=boot_file_copy.dst,
                system=system_file_copy.dst, stage=True)

    commands = None
    end_state = existing

    reboot_attempt = 'no'
    if device.staged or transfered:
        if reboot and delay:
            reboot_attempt = 'yes'
            os_reboot = Reboot(device)
            os_reboot.build(stage=True, reboot=True, delay=delay)
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands,
                      transfered=transfered,
                      end_state=end_state)
        else:
            try:
                device.execute_staged()
                end_state = ios.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error executing commands.')
            changed = True

    results = {'commands': commands, 'transfered': transfered, 'changed': changed, 'end_state': end_state}

    if reboot and not delay:
        reboot_attempt = 'yes'
        try:
            device.reboot()
            # changed = True

            # for some reason,
            # this is needed to activate the reboot
        except PYCW7Error as exe:
            safe_fail(module, msg=str(exe),
                      descr='Error rebooting the device.')

    results['reboot_attempt'] = reboot_attempt
    safe_exit(module, **results)


if __name__ == "__main__":
    main()
