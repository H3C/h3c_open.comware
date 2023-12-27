#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_startup
short_description: config the next restart file or ipe .   patch function not available,please use patch module
description:
    - Offers ability to config the restart file or config image or patch for the device.  
      Supports using .ipe or .bin system and boot packages.
version_added: 1.0.0
category: System (RW)
author: wangliang
notes:
    - The parameters ipe_package and boot/system are
      mutually exclusive.
    - makesure the files are already existing on the device.
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
    patch:
        description:
            - File (including abs path) of the local patch package (.bin)
        required: false
        type: str
    delete_ipe:
        description:
            - If ipe_package is used,
              this specifies whether the .ipe file is deleted from the device
              after it is unpacked.
        required: false
        deafult: false
        type: bool
    nextstartupfile:
        description:
            - Name of file that will be used for the next start.
        required: false
        type: str
    filename:
        description:
            - Name of file that will be show content.
        required: false
        type: str
    show_file:
        description:
            - File that will be used to store the config file content.  Relative path is
              location of ansible playbook. If not set, no file saved.
        required: false
        type: str
"""
EXAMPLES = """

#Basic Install OS Bootsys
  comware_startup:
    boot='flash:/s9850_6850-cmw710-boot-r6555p01.bin'
    system='flash:/s9850_6850-cmw710-system-r6555p01.bin'
    patch='flash:/s9850_6850-cmw710-system-patch-r6555p01h31.bin'
      
#Basic Install OS IPE

      - name: Basic Install OS Bootsys
        h3c_open.comware.comware_startup:
          boot: 'flash:/s5570s_ei-cmw710-boot-r1122.bin'
          system: 'flash:/s5570s_ei-cmw710-system-r1122.bin'
          patch: 'flash:/s5570s_ei-cmw710-system-patch-r6555p01h31.bin'

      - name: Basic Install OS IPE
        h3c_open.comware.comware_startup:
          ipe_package: 'flash:/S5570S_EI-CMW710-R1120.ipe'
    
      - name: Config next startup file
        h3c_open.comware.comware_startup:
          nextstartupfile: 'flash:/123.cfg'
"""

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file import File
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.set_startup import SetStartup
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def write_content(show_file, content):
    with open(show_file, 'w+') as diff:
        diff.write("#######################################\n")
        diff.write('####### CONTENT OF CONFIG FILE ########\n')
        diff.write("#######################################\n")
        diff.write('\n\n')
        diff.write('\n'.join(content))
        diff.write('\n')


def check_file_existing(file_lists, tname):
    for each in file_lists:
        if each == tname:
            return True
    return False


def main():
    module = AnsibleModule(
        argument_spec=dict(
            ipe_package=dict(),
            boot=dict(),
            system=dict(),
            patch=dict(),
            nextstartupfile=dict(required=False, default=None),
            filename=dict(required=False, default=None),
            show_file=dict(required=False, type='str'),
            delete_ipe=dict(choices=BOOLEANS,
                            type='bool',
                            default=False),
        ),
        supports_check_mode=True
    )

    ipe_package = module.params.get('ipe_package')
    boot = module.params.get('boot')
    system = module.params.get('system')
    patch = module.params.get('patch')
    nextstartupfile = module.params.get('nextstartupfile')
    filename = module.params.get('filename')
    show_file = module.params['show_file']

    device = get_device(module)

    changed = False
    commands = ''

    if ipe_package or boot:
        if ipe_package:
            if boot or system:
                module.fail_json(
                    msg='ipe_package and boot/system parameters are mutually exclusive')
        else:
            if not (boot and system):
                module.fail_json(
                    msg='boot and system parameters must be provided if ipe_package is not')

        already_set = False

        existing = None
        ios = None
        try:
            ios = SetStartup(device)
            existing = ios.get_reboot_config()
        except PYCW7Error as exe:
            safe_fail(module, msg=str(exe),
                      descr='Error getting current config.')

        existing_boot = existing['startup-primary']['boot']
        existing_system = existing['startup-primary']['system']
        existing_patch = existing['startup-primary']['patch']
        if patch:
            patch_basename = os.path.basename(patch)
            if ipe_package:
                ipe_basename = os.path.basename(ipe_package)
                ipe_boot_sys = re.split(r'-|\.', ipe_basename)[-3:-1]
                patch_boot_sys = re.split(r'-|\.', patch_basename)[-3:-1]
                if ipe_boot_sys:
                    if ipe_boot_sys[0].lower() in existing_boot.lower() \
                            and ipe_boot_sys[0].lower() in existing_system.lower() \
                            and ipe_boot_sys[1].lower() in existing_boot.lower() \
                            and ipe_boot_sys[1].lower() in existing_system.lower() \
                            and patch_boot_sys[0].lower() in existing_patch.lower() \
                            and patch_boot_sys[1].lower() in existing_patch.lower():
                        already_set = True

                if not already_set:
                    delete_ipe = module.params.get('delete_ipe')
                    ios.build(
                        'ipe', patch=patch, ipe=ipe_package, delete_ipe=delete_ipe, stage=True)
            elif boot:
                boot_basename = os.path.basename(boot)
                system_basename = os.path.basename(system)
                if boot_basename in existing_boot \
                        and system_basename in existing_system \
                        and patch_basename in existing_patch:
                    already_set = True

                if not already_set:
                    ios.build(
                        'bootsys', patch=patch, boot=boot, system=system, stage=True)
        else:
            if ipe_package:
                ipe_basename = os.path.basename(ipe_package)
                ipe_boot_sys = re.split(r'-|\.', ipe_basename)[-3:-1]
                if ipe_boot_sys:
                    if ipe_boot_sys[0].lower() in existing_boot.lower() \
                            and ipe_boot_sys[0].lower() in existing_system.lower() \
                            and ipe_boot_sys[1].lower() in existing_boot.lower() \
                            and ipe_boot_sys[1].lower() in existing_system.lower():
                        already_set = True

                if not already_set:
                    delete_ipe = module.params.get('delete_ipe')
                    ios.build(
                        'ipe', ipe=ipe_package, delete_ipe=delete_ipe, stage=True)
            elif boot:
                boot_basename = os.path.basename(boot)
                system_basename = os.path.basename(system)
                if boot_basename in existing_boot \
                        and system_basename in existing_system:
                    already_set = True

                if not already_set:
                    ios.build(
                        'bootsys', boot=boot, system=system, stage=True)

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
                              descr='Error executing commands.')
                changed = True

    if nextstartupfile:

        startup_file = File(device, filename=nextstartupfile)
        f_lists = startup_file.get_rollback_file_lists()
        if "flash:/" not in nextstartupfile:
            module.fail_json(msg="please make sure the file is the full path in the flash")
        if nextstartupfile[-4:] != '.cfg':
            module.fail_json(msg='filename should end with .cfg')
        if not check_file_existing(f_lists, nextstartupfile):
            module.fail_json(
                msg='file {0} not in the flash,please check the name of the startup file'.format(nextstartupfile))
        try:
            startup_file.build_startupfile(nextstartupfile)
        except PYCW7Error as exe:
            safe_fail(module, msg=str(exe),
                      descr='Failed to set startup file.')
        changed = True

    if filename and show_file:

        config_file = File(device, filename=filename)
        f_lists = config_file.get_rollback_file_lists()
        if "flash:/" not in filename:
            module.fail_json(msg="please make sure the file is the full path in the flash")
        if filename[-4:] != '.cfg':
            module.fail_json(msg='filename should end with .cfg')
        if not check_file_existing(f_lists, filename):
            module.fail_json(
                msg='file {0} not in the flash,please check the name of the startup file'.format(filename))
        try:
            filecontent = config_file.get_file_content()
            write_content(show_file, filecontent)
        except PYCW7Error as exe:
            safe_fail(module, msg=str(exe),
                      descr='Failed to get content for the file.')

        changed = True

    results = {'commands': commands, 'changed': changed}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
