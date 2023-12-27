#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_log_source
short_description: Manage output rules for log information on V7 devices
description:
    - Manage output rules for log information on V7 devices
version_added: 1.0.0
author: gongqianyu
category: Feature (RW)
notes:
    - If state=default, the config will be removed
options:
    channelID:
        description:
            - Specifies syslog output destination
        required: True
        choices: ['1', '2', '3', '4', '5'] 
                 # 1:Console 2:Monitor terminal 3:Log buffer 4:Log host 5:Log file
        type: str
    channelName:
        description:
            - Specifies a module by its name.
        required: True
        type: str
    level:
        description:
            - A log output rule specifies the source modules and severity level of logs 
              that can be output to a destination. Logs matching the output rule are output to the destination.
        required: False
        choices: ['emergency', 'alert', 'critical', 'error', 'warning', 
                  'notification', 'informational', 'debugging', 'deny']
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

  - name: Basic config
    h3c_open.comware.comware_log_source:
      channelID=1 
      channelName=ARP 
      level=critical
  
  - name: Delete config
    h3c_open.comware.comware_log_source:
      channelID=1 
      channelName=ARP 
      level=critical 
      state=absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.syslog import Source
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    LengthOfStringError, VlanIDError)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            channelID=dict(required=True, type='str', choices=['1', '2', '3', '4', '5']),
            channelName=dict(required=True, type='str'),
            level=dict(required=False, type='str',
                       choices=['emergency', 'alert', 'critical', 'error', 'warning', 'notification', 'informational',
                                'debugging', 'deny']),

            state=dict(required=False, choices=['present', 'absent'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    channelID = module.params['channelID']
    channelName = module.params['channelName']
    level = module.params['level']
    state = module.params['state']

    args = dict(channelID=channelID, channelName=channelName, level=level)
    proposed = dict((k, v) for k, v in args.items() if v is not None)
    changed = False
    src_obj = None
    try:
        src_obj = Source(device, channelID, channelName, level)

    except LengthOfStringError as lose:
        module.fail_json(msg=str(lose))
    except VlanIDError as vie:
        module.fail_json(msg=str(vie))
    except PYCW7Error as e:
        module.fail_json(msg=str(e))
    existing = None
    try:
        existing = src_obj.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error getting syslog source config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            src_obj.build(stage=True)

    elif state == 'absent':
        if existing:
            src_obj.remove(stage=True)

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
                end_state = src_obj.get_config()
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
