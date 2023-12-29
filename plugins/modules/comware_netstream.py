#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_netstream
short_description: Manage ip netstream,rate,timeout, max_entry,vxlan udp-port,and interface enable and ip netstream
                aggregation destination-prefix enable,
                netstream statistics output message destination address and destination UDP port number configurationon
                Comware 7 devices
description:
    - Manage ip netstream,rate,timeout, max_entry,vxlan udp-port,and interface enable and ip netstream
      aggregation destination-prefix enable, netstream statistics output message destination address and
      destination UDP port number configurationon Comware 7 devices
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - Before configuring netstream stream image, you need to enable the global netstream function.
    - The default state is not open global netstream function.If you want to config interface netstream enable,the name
      parameter must be exit.If you config netstream statistics output message,host and udp paramaters must be exit.
options:
    netstream:
        description:
            -  global netstream enable or disable
        required: false
        choices: ['enable', 'disabled']
        type: str
    rate:
        description:
            -  Configure output rate limit
        required: false
        type: str
    timeout:
        description:
            -  Active aging time of configuration flow
        required: false
        type: str
    max_entry:
        description:
            -  Active aging time of configuration flow
        required: false
        type: str
    vxlan_udp:
        description:
            -  Enable vxlan message statistics function
        required: false
        type: str
    sampler:
        description:
            - Create a sampler.
        required: false
        type: str
    mode:
        description:
            - Sampler mode.if config sampler,this parameter is must be exit.
        required: false
        choices: ['fixed', 'random']
        type: str
    sampler_rate:
        description:
            - Sampler rate. if config sampler,this parameter is must be exit.
        required: false
        type: str
    version:
        description:
            - Configure autonomous system options for netstream version.
        required: false
        choices: ['5', '9', '10']
        default: '9'
        type: str
    BGP:
        description:
            - Configure bgp.
        required: false
        choices: ['origin-as', 'peer-as', 'bgp-nexthop']
        type: str
    inactive:
        description:
            - Configure Inactive aging time of flow.(10~600).
        required: false
        type: str
    source_intf:
        description:
            - Configure the source interface of netstream statistical output message.
        required: false
        type: str
    aggregation:
        description:
            - Enter netstream aggregation view and enable it
        required: false
        choices: ['as', 'destination-prefix', 'prefix', 'prefix-port', 'protocol-port',
                  'source-prefix', 'tos-as', 'tos-bgp-nexthop', 'tos-destination-prefix',
                  'tos-prefix', 'tos-protocol-port', 'tos-source-prefix']
        type: str
    name:
        description:
            - Full name of the interface
        required: false
        type: str
    interface_enable:
        description:
            - manage interface netstream enable.To config this, name parameter must be exit.
        required: false
        choices: ['inbound', 'outbound']
        type: str
    interface_sampler:
        description:
            - manage interface sampler.
        required: false
        type: str
    host:
        description:
            - Configure the destination address of netstream statistical output message.
        required: false
        type: str
    udp:
        description:
            - Configure the destination UDP port number of netstream statistical output message.
        required: false
        type: str
    vpn_name:
        description:
            - Specify the VPN to which the destination address of netstream statistical output message belongs.
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration.
        required: false
        choices: ['present', 'absent']
        default: present
        type: str
"""

EXAMPLES = """

      - name: netstream config
        h3c_open.comware.comware_netstream:
          netstream: enable
          rate: 10
          timeout: 1
          max_entry: 2
          vxlan_udp: 8000
          aggregation: prefix
          host: 192.168.1.43
          udp: 29
          state: present

      - name: delete netstream config
        h3c_open.comware.comware_netstream:
          netstream: enable
          rate: 10
          timeout: 1
          max_entry: 2
          vxlan_udp: 8000
          aggregation: prefix
          host: 192.168.1.43
          udp: 29
          state: absent

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.netstream import Netstream
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (get_device)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            netstream=dict(required=False, choices=['enable', 'disabled']),
            rate=dict(required=False),
            timeout=dict(required=False),
            max_entry=dict(required=False),
            vxlan_udp=dict(required=False),
            sampler=dict(required=False),
            mode=dict(required=False, choices=['fixed', 'random']),
            sampler_rate=dict(required=False),
            aggregation=dict(required=False,
                             choices=['as', 'destination-prefix', 'prefix', 'prefix-port', 'protocol-port',
                                      'source-prefix', 'tos-as', 'tos-bgp-nexthop', 'tos-destination-prefix',
                                      'tos-prefix', 'tos-protocol-port', 'tos-source-prefix']),
            version=dict(required=False, choices=['5', '9', '10'], default='9'),
            BGP=dict(required=False, choices=['origin-as', 'peer-as', 'bgp-nexthop']),
            inactive=dict(required=False),
            source_intf=dict(required=False),
            name=dict(required=False),
            interface_enable=dict(required=False, choices=['inbound', 'outbound']),
            interface_sampler=dict(required=False),
            host=dict(required=False),
            udp=dict(required=False),
            vpn_name=dict(required=False),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    netstream = module.params['netstream']
    interface_sampler = module.params['interface_sampler']
    sampler = module.params['sampler']
    mode = module.params['mode']
    sampler_rate = module.params['sampler_rate']
    rate = module.params['rate']
    timeout = module.params['timeout']
    max_entry = module.params['max_entry']
    vxlan_udp = module.params['vxlan_udp']
    aggregation = module.params['aggregation']
    version = module.params['version']
    BGP = module.params['BGP']
    inactive = module.params['inactive']
    source_intf = module.params['source_intf']
    name = module.params['name']
    interface_enable = module.params['interface_enable']
    host = module.params['host']
    udp = module.params['udp']
    vpn_name = module.params['vpn_name']
    state = module.params['state']
    args = dict(netstream=netstream, rate=rate, timeout=timeout, max_entry=max_entry, vxlan_udp=vxlan_udp,
                sampler=sampler, mode=mode, sampler_rate=sampler_rate, interface_sampler=interface_sampler,
                aggregation=aggregation, version=version, BGP=BGP, inactive=inactive, source_intf=source_intf,
                name=name, interface_enable=interface_enable, host=host, udp=udp, vpn_name=vpn_name)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    changed = False

    netStream = None
    try:
        netStream = Netstream(device, netstream, rate, timeout, max_entry, vxlan_udp, sampler, mode, sampler_rate,
                              interface_sampler, aggregation, version, BGP, inactive, source_intf, name,
                              interface_enable, host, udp, vpn_name)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    if state == 'present':
        netStream.build(stage=True)
    elif state == 'absent':
        netStream.remove(stage=True)

    commands = None

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
                          descr='error during execution')
            changed = True

    results = {'state': state, 'commands': commands, 'changed': changed, 'proposed': proposed}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
