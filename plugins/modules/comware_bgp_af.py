#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_bgp_af
short_description: Manage address family configs
description:
    - Manage address family configs such as ipv4 ipv6 .
version_added: 1.0.0
category: Feature (RW)
author: hanyangyang
notes:
    - Address family vpnv4 and vpnv6 has no parameter 'local_pref','frr_policy','policy_target'
      and 'allow_invalid_as'.
    - Different af options cannot be configured at the same time , for example , address family
      ipv4 and ipv6 must be config in different task.
    - Default state will directly delete bgp as, please use it with carefully
options:
    bgp_as:
        description:
            - Autonomous system number <1-4294967295>
        required: True
        type: str
    bgp_instance:
        description:
            - Specify a BGP instance by its name
        required: false
        type: str
    address_familys:
        description:
            - Specify an address family
        required: false
        type: str
    local_pref:
        description:
            - Set the default local preference value
        required: false
        type: str
    frr_policy:
        description:
            - Configure fast reroute policy
        required: false
        default: false
        type: bool
    policy_target:
        description:
            - Filter VPN4 routes with VPN-Target attribute
        required: false
        default: true
        type: bool
    route_select_delay:
        description:
            - Set the delay time for optimal route selection
        required: false
        type: str
    allow_invalid_as:
        description:
            - Apply the origin AS validation state to optimal route selection
        required: false
        type: bool
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        type: str
"""
EXAMPLES = """
       - name: Configue bgp ipv4 address family
        h3c_open.comware.comware_bgp_af:
          bgp_as: 10
          bgp_instance: test
          address_familys: ipv4
          local_pref: 20
          frr_policy: true
        register: results

      - name: Configue bgp vpnv4 address family
        h3c_open.comware.comware_bgp_af:
          bgp_as: 10
          bgp_instance: test
          address_familys: vpnv4
          route_select_delay: 20

"""

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.bgp_af import Bgp
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    BgpAfParamsError, BgpAfConfigError)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            bgp_as=dict(required=True, type='str'),
            bgp_instance=dict(required=False, type='str'),
            address_familys=dict(choices=['ipv4', 'ipv6', 'vpnv4', 'vpnv6']),
            local_pref=dict(type='str'),
            frr_policy=dict(choices=['true', 'false']),
            policy_target=dict(choices=['true', 'false']),
            route_select_delay=dict(type='str'),
            allow_invalid_as=dict(choices=['true', 'false']),
            state=dict(choices=['present', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    bgp_as = module.params['bgp_as']
    bgp_instance = module.params['bgp_instance']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    bgp = None
    try:
        bgp = Bgp(device, )
    except BgpAfParamsError as params_e:
        safe_fail(module, msg=str(params_e))
    except BgpAfConfigError as config_e:
        safe_fail(module, msg=str(config_e))
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    try:
        bgp.param_check(**proposed)
    except PYCW7Error as exe:
        safe_fail(module, descr='There was problem with the supplied parameters.',
                  msg=str(exe))

    existing = None
    try:
        existing = bgp.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting existing config.')

    if state == 'present':
        delta = proposed
        if delta:
            bgp.build_bgp_af(stage=True, **delta)

    elif state == 'default':
        default_bgp = dict(bgp_as=bgp_as,
                           bgp_instance=bgp_instance)
        bgp.remove_bgp(stage=True, **default_bgp)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = bgp.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
