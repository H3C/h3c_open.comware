#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_reboot
short_description: Perform a reboot of a Comware 7 device
description:
    - Offers ability to reboot Comware 7 devices instantly
      at a scheduled time, or after a given period of time
version_added: 1.0.0
category: System (RW)
notes:
    - Time/date and delay are mutually exclusive parameters
    - Time is required when specifying date
    - Reboot must be set to true to reboot the device
    - This module is not idempotent
options:
    reboot:
        description:
            - Needs to be set to true to reboot the device
        required: true
        type: bool
    time:
        description:
            - Specify the time at which the reboot will take place.
              Format should be HH:MM enclosed in quotes.
        required: false
        type: str
    date:
        description:
            - Specify the date at which the reboot will take place.
              The time parameter is required to use this parameter.
              Format should be MM/DD/YYYY in quotes.
        required: false
        type: str
    delay:
        description:
            - Delay (in minutes) to wait to reboot the device
        required: false
        type: str

"""

EXAMPLES = """

- name: Fail when reboot param isnt included
  h3c_open.comware.comware_reboot:
  ignore_errors: true
  register: results

- name: Validate fail TEST 1
  assert:
    that:
      - results.failed == true

- name: Reboot at 5:00
  h3c_open.comware.comware_reboot:
    reboot: true
    time: "05:00"

- name: Reboot in 5 minutes
  h3c_open.comware.comware_reboot:
    reboot: true
    delay: 5

- name: Reboot at 22:00 on Dec 21 2023
  h3c_open.comware.comware_reboot:
    reboot: true
    time: "22:00"
    date: "12/21/2023"

# uncomment to reboot!!!
# - name: Reboot immedidately
#   h3c_open.comware.comware_reboot:
#     reboot:true
#   tags: now
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import BOOLEANS
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import NCTimeoutError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    RebootDateError, RebootTimeError, PYCW7Error
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.reboot import Reboot


def main():
    module = AnsibleModule(
        argument_spec=dict(
            reboot=dict(required=True, choices=BOOLEANS, type='bool'),
            delay=dict(required=False, type='str'),
            date=dict(required=False, type='str'),
            time=dict(required=False, type='str'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    reboot = module.params['reboot']
    delay = module.params['delay']
    date = module.params['date']
    time = module.params['time']

    if date:
        if not time:
            module.fail_json(msg='time is also required when specifying date')

    proposed = dict(reboot=reboot, delay=delay,
                    time=time, date=date)
    reboot_me = None

    try:
        reboot_me = Reboot(device)
        reboot_me.param_check(**proposed)
    except RebootDateError as rde:
        module.fail_json(msg=str(rde))
    except RebootTimeError as rte:
        module.fail_json(msg=str(rte))
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error using Reboot object')

    reboot_me.build(stage=True, **proposed)

    commands = None
    response = None
    changed = False

    results = {}

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                response = device.execute_staged()
                changed = True
            except PYCW7Error as e:
                if isinstance(e, NCTimeoutError):
                    results['changed'] = True
                    results['rebooted'] = True
                    results['commands'] = commands
                    module.exit_json(**results)
                else:
                    module.fail_json(msg=str(e),
                                     descr='error during execution')

    results['proposed'] = proposed
    results['commands'] = commands
    results['changed'] = changed
    results['end_state'] = 'N/A for this module'
    results['response'] = response

    module.exit_json(**results)


if __name__ == "__main__":
    main()
