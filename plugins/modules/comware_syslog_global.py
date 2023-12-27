#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_syslog_global
short_description: Manage system log timestamps and  terminal logging level on Comware 7 devices
version_added: 1.0.0
author: gongqianyu
category: Feature (RW)
notes:
    - Before configuring this,the global syslog need to be enabled.
    - The timestamps default state is data, terminal logging level default is 6.
options:
    timestamps:
        description:
            - Configure the time stamp output format of log information sent to the console, monitoring terminal, 
               log buffer and log file direction.
        required: False
        default: date
        type: str
    level:
        description:
            - Configure the minimum level of log information that the current terminal allows to output.
        required: False
        default: informational
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        type: str

"""

EXAMPLES = """

        - name: timestamps and level config
        h3c_open.comware.comware_syslog_global:
          timestamps: boot
          level: debugging
        register: results

      - name: Restore timestamps and level to default state
        h3c_open.comware.comware_syslog_global:
          timestamps: boot
          level: debugging
          state: absent
        register: results

"""

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.syslog_global import Syslog
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            timestamps=dict(required=False, choices=['boot', 'date', 'none'], default='date'),
            level=dict(required=False,
                       choices=['alert', 'critical', 'debugging', 'emergency', 'error', 'informational', 'notification',
                                'warning'], default='informational'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    timestamps = module.params['timestamps']
    level = module.params['level']
    state = module.params['state']
    args = dict(timestamps=timestamps, level=level)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    changed = False

    sysLog = None
    try:
        sysLog = Syslog(device, timestamps, level)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    if state == 'present':
        sysLog.build(stage=True)
    elif state == 'absent':
        sysLog.remove(stage=True)

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
