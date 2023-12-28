#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = '''
---

module: comware_save
short_description: Save the running configuration
description:
    - Save the running configuration
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - This modules saves the running config as startup.cfg, or the supplied
      filename, in flash. It is not
      changing the config file to load on next boot.
options:
    filename:
        description:
            - Name of file that will be used when saving the current
              running conifg to flash.
        required: false
        default: startup.cfg
        type: str

'''
EXAMPLES = '''

- name: Save as myfile.cfg (in flash)
  h3c_open.comware.comware_save:
    filename: myfile.cfg
  register: results

- name: Save as startup.cfg (in flash)
  h3c_open.comware.comware_save:
  register: results

'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import PYCW7Error


def main():

    module = AnsibleModule(
        argument_spec=dict(
            filename=dict(required=False, default='startup.cfg'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    filename = module.params['filename']

    if "/" in filename:
        module.fail_json(msg="specify only filename. it'll be saved in flash")
    if filename[-4:] != '.cfg':
        module.fail_json(msg='filename should end with .cfg')

    changed = False

    device.stage_config('{0}'.format(filename), "save")

    commands = None
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
