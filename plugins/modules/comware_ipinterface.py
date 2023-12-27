#!/usr/bin/python

DOCUMENTATION = """
---
module: comware_ipinterface
short_description: Manage IPv4/IPv6 addresses on interfaces
description:
    - Manage IPv4/IPv6 addresses on interfaces
version_added: 1.0.0
category: Feature (RW)
notes:
    - If the interface is not configured to be a layer 3 port,
      the module will fail and the user should use the interface
      module to convert the interface with type=routed
    - If state=absent, the specified IP address will be removed from the interface.
      If the existing IP address doesn't match the specified,
      the existing will not be removed.
options:
    name:
        description:
            - Full name of the interface
        required: true
        type: str
    addr:
        description:
            - The IPv4 or IPv6 address of the interface
        required: true
        type: str
    mask:
        description:
            - The network mask, in dotted decimal or prefix length notation.
              If using IPv6, only prefix length is supported.
        required: true
        type: str
    version:
        description:
            - v4 for IPv4, v6 for IPv6
        required: false
        default: v4
        type: str
    state:
        description:
            - Desired state of the switchport
        required: false
        default: present
        type: str
    
"""

EXAMPLES = """

      - name: ensure layer 3
        h3c_open.comware.comware_interface:
          name: HundredGigE1/0/25
          type: routed
        register: results

      - assert:
          that:
            - "results.end_state.type == 'routed'"

      - name: Basic IPv4 config
        h3c_open.comware.comware_ipinterface:
          name: HundredGigE1/0/25
          addr: 192.168.3.5
          mask: 255.255.255.0
        register: results

      - assert:
          that:
            - "results.end_state.addr == '192.168.3.5'"
            - "results.end_state.mask == '255.255.255.0'"

"""
import ipaddr
from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.ipinterface import IpInterface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.validate import valid_ip_network
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *


def compare_ips(net1, net2):
    x = ipaddr.IPNetwork(net1)
    y = ipaddr.IPNetwork(net2)
    return x.ip == y.ip \
        and x.prefixlen == y.prefixlen


def ip_stringify(**kwargs):
    return kwargs.get('addr') + '/' + kwargs.get('mask')


def get_existing(ip_int, addr, mask):
    existing_list = ip_int.get_config()
    for each in existing_list:
        if each:
            if compare_ips(
                    ip_stringify(**each), ip_stringify(addr=addr, mask=mask)):
                return each
    return {}


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            addr=dict(required=True),
            mask=dict(required=True, type='str'),
            version=dict(choices=['v4', 'v6'],
                         default='v4'),
            state=dict(choices=['present', 'absent'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'version', 'look_for_keys')

    device = get_device(module)

    name = module.params['name']
    state = module.params['state']
    version = module.params['version']
    addr = module.params['addr']
    mask = module.params['mask']
    changed = False

    if not valid_ip_network(ip_stringify(**module.params)):
        module.fail_json(msg='Not a valid IP address or mask.')

    ip_int = None
    try:
        ip_int = IpInterface(device, name, version)
    except PYCW7Error as exe:
        safe_fail(module, descr='There was an error initializing'
                                + ' the IpInterface class.',
                  msg=str(exe))

    if not ip_int.interface.iface_exists:
        safe_fail(module, msg='Please use the interface module ' +
                              'to create the {0} interface.'.format(ip_int.interface_name))

    # Make sure interface is routed
    if not ip_int.is_routed:
        safe_fail(module, msg='Please use the interface module ' +
                              'to make {0} a routed interface.'.format(ip_int.interface_name))

    existing = None
    try:
        existing = get_existing(ip_int, addr, mask)
    except PYCW7Error as exe:
        safe_fail(module,
                  descr='Error getting the existing configuration.',
                  msg=str(exe))

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if existing:
        ips_are_same = compare_ips(
            ip_stringify(**existing), ip_stringify(**proposed))
    else:
        ips_are_same = False

    if state == 'present':
        if not ips_are_same:
            ip_int.build(stage=True, **proposed)
    elif state == 'absent':
        if ips_are_same:
            ip_int.remove(stage=True, **existing)

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
                end_state = get_existing(ip_int, addr, mask)
            except PYCW7Error as exe:
                safe_fail(module,
                          descr='Error during command execution.',
                          msg=str(exe))
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
