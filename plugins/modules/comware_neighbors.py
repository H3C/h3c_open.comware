#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_neighbors
short_description: Retrieve active LLDP neighbors (read-only)
description:
    - Retrieve active LLDP neighbors (read-only)
version_added: 1.0.0
author: h3c (@h3c_open)
options:
    neigh_type:
        description:
            - type of neighbors
        required: false
        choices: ['cdp', 'lldp']
        default: lldp
        type: str
"""

EXAMPLES = '''

        - name: get lldp neighbors
          h3c_open.comware.comware_neighbors:
            neigh_type: lldp

        - name: dump all of results
          debug: var=response.neighbors


'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.neighbor import Neighbors
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            neigh_type=dict(default='lldp', choices=['cdp', 'lldp']),
        ),
        supports_check_mode=False
    )

    device = get_device(module)
    neigh_type = module.params['neigh_type']

    neighbors = None
    try:
        neighbors = Neighbors(device)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='error getting neighbor info')

    response = getattr(neighbors, neigh_type)

    results = dict(neighbors=response)
    safe_exit(module, **results)


if __name__ == "__main__":
    main()
