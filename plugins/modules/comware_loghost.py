#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_loghost
short_description: Manage info-center log host and related parameters on V7 devices
description:
    - Manage info-center log host and related parameters on V7 devices
version_added: 1.0.0
author: gongqianyu
category: Feature (RW)
options:
    loghost:
        description:
            - Address of the log host
        required: True
        type: str
    VRF:
        description:
            - VRF instance name
        required: True
        type: str
    hostport:
        description:
            - Port number of the log host.
        required: False
        default: 514
        type: str
    facility:
        description:
            - Logging facility used by the log host.
        required: False
        default: 184
        choices: ['128', '136', '144', '152', '160', '168', '176', '184'] 
                 # 128:local0, 136:local1 144:local2 152:local3 160:local4 168:local5 176:local6 184:local7
        type: str
    sourceID:
        description:
            - Configure the source IP address of the sent log information. \
            The default state is Using the primary IP address of \
            the outgoing interface as the source IP address of the sent log information
        required: False
        type: str
    state:
        description:
            - Desired state of the switchport
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
"""
EXAMPLES = """
- name: basic config
  h3c_open.comware.comware_loghost:
    loghost: 3.3.3.7 
    VRF: vpn2 
    hostport: 512 
    facility: 128 
    sourceID: LoopBack0

- name: delete config
  h3c_open.comware.comware_loghost:
    loghost: 3.3.3.7 
    VRF: vpn2 
    hostport: 512 
    facility: 128 
    sourceID: LoopBack0 
    state: absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.syslog import Loghost


def main():
    module = AnsibleModule(
        argument_spec=dict(
            loghost=dict(required=True, type='str'),
            VRF=dict(required=True, type='str'),
            hostport=dict(required=False, type='str', default='514'),
            facility=dict(required=False, choices=['128', '136', '144', '152', '160', '168', '176', '184'], type='str',
                          default='184'),
            sourceID=dict(required=False, type='str'),
            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    loghost = module.params['loghost']
    VRF = module.params['VRF']
    hostport = module.params['hostport']
    facility = module.params['facility']
    source_id = module.params['sourceID']

    state = module.params['state']

    args = dict(loghost=loghost, VRF=VRF, hostport=hostport, facility=facility, sourceID=source_id)
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    changed = False
    log_host = None
    try:
        log_host = Loghost(device, loghost, VRF, hostport, facility)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))
    existing = {}
    try:
        existing = log_host.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting loghost config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            log_host.build(stage=True)
        if module.params.get('sourceID'):
            log_host.build_time(stage=True, sourceID=source_id)

    elif state == 'absent':
        if existing:
            log_host.remove(stage=True)
        if module.params.get('sourceID'):
            log_host.build_time_absent(stage=True, sourceID=source_id)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = log_host.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='Error during command execution.')
            changed = True

    results = {}
    results['proposed'] = proposed
    results['existing'] = existing
    results['state'] = state
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = end_state

    module.exit_json(**results)


if __name__ == "__main__":
    main()
