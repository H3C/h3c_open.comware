#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_clean_erase
short_description: Factory default Comware 7 device
description:
    - Reset system to factory default settings.  You will
      lose connectivity to the switch.  This module deletes all configuration
      files (.cfg files) in the root directories of the storage media.
      It deletes all log files (.log files in the folder /logfile). Clears
      all log information (in the log buffer), trap information, and debugging
      information. Restores the parameters for the Boot ROM options to the
      factory-default settings. Deletes all files on an installed
      hot-swappable storage medium, such as a USB disk
version_added: 1.0.0
author: h3c (@h3c_open)
options:
    factory_default:
        description:
            - Set to true if all logs and user-created files
              should be deleted and removed from the system
              and the device should be set to factory default
              settings
        required: false
        default: false
        type: bool

"""
EXAMPLES = """

      - name: factory default and reboot immediately
        h3c_open.comware.comware_clean_erase:
          factory_default: true
        register: results

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.cleanerase import CleanErase
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error, NCTimeoutError


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            factory_default=dict(default=False, type='bool'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    factory_default = module.params['factory_default']

    clean_erase = None
    try:
        clean_erase = CleanErase(device)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='error initializing CleanErase')

    if factory_default:
        clean_erase.build(stage=True, factory_default=factory_default)

    results = {'changed': False, 'rebooted': False, 'commands': None}

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
            except PYCW7Error as exe:
                if isinstance(exe, NCTimeoutError):
                    results['changed'] = True
                    results['rebooted'] = True
                    results['commands'] = commands
                    module.exit_json(**results)
                else:
                    safe_fail(module, msg=str(exe),
                              descr='error during execution')

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
