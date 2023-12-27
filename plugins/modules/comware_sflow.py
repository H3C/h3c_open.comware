#!/usr/bin/python


DOCUMENTATION = """
---

module: comware_sflow
short_description: Manage sflow attributes for Comware 7 devices
description:
    - Manage sflow attributes for Comware 7 devices
version_added: 1.0.0
category: Feature (RW)
options:
    collectorID:
        description:
            - the sflow collector id
        required: true
        type: str
    addr:
        description:
            - the ipv4 or ipv6 address 
        required: true
        type: str
    vpn:
        description:
            - Name to configure for the specified vpn-instance
        required: false
        type: str
    descr:
        description:
            - Description for the collectorID.must be exit
        required: false
        default: CLI Collector
        type: str
    time_out:
        description:
            - the collector's parameter aging time
        required: false
        type: int
    Port:
        description:
            -   UDP port
        required: false
        default: 6343
        type: int
    data_size:
        description:
            - the sflow datagram max size
        required: false
        default: 1400
        type: int
    agent_ip:
        description:
            - Configure the IP address of the sFlow agent.
        required: false
        type: str
    sourceIpv4IP:
        description:
            - Configure the source IPV4 address of the sFlow message.
        required: false
        type: str
    sourceIpv6IP:
        description:
            - Configure the source IPV6 address of the sFlow message.
        required: false
        type: str
"""
EXAMPLES = """
- name: Basic  config
  h3c_open.comware.comware_sflow:
    collectorID: 1 
    vpn: 1 
    addr: 1.1.1.1 
    data_size: 500 
    descr: netserver 
    time_out: 1200

- name: delete config
  h3c_open.comware.comware_sflow:
    collectorID: 1 
    addr: 1.1.1.1 
    state: absent 
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.sflow import SFlow
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.sflow import Sflow


def main():
    module = AnsibleModule(
        argument_spec=dict(
            collectorID=dict(required=True, type='str'),
            addr=dict(type='str', required=True),
            vpn=dict(type='str', required=False),
            descr=dict(type='str', required=False),
            data_size=dict(required=False),
            time_out=dict(required=False),
            sourceIpv4IP=dict(type='str', required=False),
            sourceIpv6IP=dict(type='str', required=False),
            agent_ip=dict(type='str', required=False),
            Port=dict(required=False),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    collectorID = module.params['collectorID']
    addr = module.params['addr']
    descr = module.params['descr']
    vpn = module.params['vpn']
    state = module.params['state']
    data_size = module.params['data_size']
    time_out = module.params['time_out']
    Port = module.params['Port']
    sourceIpv4IP = module.params['sourceIpv4IP']
    sourceIpv6IP = module.params['sourceIpv6IP']
    agent_ip = module.params['agent_ip']

    changed = False

    args = dict(collectorID=collectorID, addr=addr, descr=descr, vpn=vpn, time_out=time_out, data_size=data_size,
                Port=Port, sourceIpv4IP=sourceIpv4IP, sourceIpv6IP=sourceIpv6IP, agent_ip=agent_ip)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    results = {}
    results['proposed'] = proposed

    sflow = None
    sFlow = None
    try:
        if collectorID and (sourceIpv4IP or sourceIpv6IP or agent_ip):
            sflow = Sflow(device, collectorID)
            sFlow = SFlow(device, sourceIpv4IP, sourceIpv6IP, agent_ip)
        elif sourceIpv4IP or sourceIpv6IP or agent_ip and not collectorID:

            sFlow = SFlow(device, sourceIpv4IP, sourceIpv6IP, agent_ip)
        else:

            sflow = Sflow(device, collectorID)
            sflow.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    existing = {}
    existing_1 = {}
    try:
        if collectorID and (sourceIpv4IP or sourceIpv6IP or agent_ip):
            existing = sflow.get_config()
            existing_1 = sFlow.get_config()
        elif sourceIpv4IP or sourceIpv6IP or agent_ip and not collectorID:
            existing_1 = sFlow.get_config()
        else:
            existing = sflow.get_config()

    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error getting vlan config')
    sFlow = SFlow(device, sourceIpv4IP, sourceIpv6IP, agent_ip)
    # sFlow.remove(stage=True)
    if collectorID and (sourceIpv4IP or sourceIpv6IP or agent_ip):
        pass

    if state == 'present':
        if collectorID and (sourceIpv4IP or sourceIpv6IP or agent_ip):
            delta = dict(set(proposed.items()).difference(existing.items()))
            delta_1 = dict(set(proposed.items()).difference(existing_1.items()))
            if delta:
                sflow.build(stage=True, **delta)
            if delta_1:
                sFlow.build(stage=True, **delta_1)

        elif sourceIpv4IP or sourceIpv6IP or agent_ip and not collectorID:
            if agent_ip:
                sFlow.debug(stage=True)
            delta_1 = dict(set(proposed.items()).difference(existing_1.items()))
            if delta_1:
                sFlow.build(stage=True, **delta_1)
            if delta_1:
                sFlow.build(stage=True, **delta_1)

        else:

            delta = dict(set(proposed.items()).difference(existing.items()))
            if delta:
                sflow.build(stage=True, **delta)

    elif state == 'absent':
        if sourceIpv4IP or sourceIpv6IP or agent_ip and not collectorID:
            sFlow.remove(stage=True)
        elif collectorID and (sourceIpv4IP or sourceIpv6IP or agent_ip):
            if existing:
                sflow.remove(stage=True)
            if existing_1:
                sFlow.remove(stage=True)
        else:
            if existing:
                sflow.remove(stage=True)

    if sourceIpv4IP or sourceIpv6IP or agent_ip and not collectorID:
        pass
    commands = None
    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            device.close()
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
                if collectorID and (sourceIpv4IP or sourceIpv6IP or agent_ip):
                    end_state = sflow.get_config()
                    end_state_1 = sFlow.get_config()

                    results['existing'] = existing
                    results['end_state_1'] = end_state_1
                    results['existing_1'] = existing_1
                    results['end_state'] = end_state

                elif sourceIpv4IP or sourceIpv6IP or agent_ip and not collectorID:
                    end_state_1 = sFlow.get_config()

                    results['end_state_1'] = end_state_1

                else:

                    end_state = sflow.get_config()
                    results['end_state'] = end_state
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')
            changed = True

    results['state'] = state
    results['commands'] = commands
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
