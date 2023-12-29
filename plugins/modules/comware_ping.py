#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_ping
short_description: Ping remote destinations *from* the Comware 7 switch
description:
    - Ping remote destinations *from* the Comware 7 device.  Really helpful
      for reachability testing.
version_added: 1.0.0
author: h3c (@h3c_open)
options:
    host:
        description:
            - IP or name (resolvable by the switch) that you want to ping
        required: true
        type: str
    vrf:
        description:
            - VRF instance pings should be sourced from
        required: false
        type: str
    v6:
        description:
            -  Whether the IP is IPV6
        required: false
        default: false
        type: bool
"""
EXAMPLES = """

  - name: test reachability to 8.8.8.8
    h3c_open.comware.comware_ping:
      host: 8.8.8.8
    register: results

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import (
    PYCW7Error
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    InvalidIPAddress
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.ping import Ping


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(required=True, type='str'),
            vrf=dict(required=False, type='str'),
            v6=dict(default=False, type='bool'),
        ),
        supports_check_mode=False
    )

    device = get_device(module)
    host = module.params['host']
    vrf = module.params['vrf']
    v6 = module.params['v6']

    ping = None
    try:
        ping = Ping(device, host, vrf=vrf, v6=v6)
    except InvalidIPAddress as iie:
        module.fail_json(msg=str(iie))
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    response = ping.response

    results = dict(response=response)
    module.exit_json(**results)


if __name__ == "__main__":
    main()
