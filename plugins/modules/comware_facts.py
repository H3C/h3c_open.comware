#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_facts
short_description: Gather facts of Comware 7 devices
description:
    - Gather fact data (characteristics) of Comware 7 devices
version_added: 1.0.0
author: h3c (@h3c_open)
"""
EXAMPLES = """

  - name: Get facts
    h3c_open.comware.comware_facts:

"""
RETURNS = """
return_data:
    - vendor
    - model
    - serial_number
    - uptime
    - hostname
    - os
    - localtime
    - config (name of running config)
    - interface_list
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.facts import Facts


def main():
    module = AnsibleModule(
        argument_spec=dict(
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    facts = None
    try:
        facts = Facts(device)
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error collecting facts')

    device_facts = facts.facts

    module.exit_json(ansible_facts=device_facts)


if __name__ == "__main__":
    main()
