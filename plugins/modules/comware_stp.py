#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_stp
short_description: Manage stp global BPDU enable, working mode and tc-bpdu attack protection function.
description:
    - 
version_added: 1.0.0
category: Feature (RW)
author: hanyangyang
notes:

options:
    bpdu:
        description:
            - Turn on the global BPDU protection function.
        required: false
        type: bool
    mode:
        description:
            - Configure the working mode of the spanning tree.
        required: false
        type: str
    tc:
        description:
            - Enable anti tc-bpdu attack protection function.
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

      - name: Basic stp config
        h3c_open.comware.comware_stp:
          bpdu: true
          mode: MSTP
          tc: true

      - name: delete Basic stp config
        h3c_open.comware.comware_stp:
          bpdu: true
          mode: MSTP
          tc: true
          state: absent

"""

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.stp import Stp
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            bpdu=dict(required=False, choices=['true', 'false', ]),
            mode=dict(required=False, choices=['MSTP', 'PVST', 'RSTP', 'STP']),
            tc=dict(required=False, choices=['true', 'false', ]),
            state=dict(choices=['present', 'absent', 'default'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    stp = None
    try:
        stp = Stp(device, )
    except PYCW7Error as exe:
        safe_fail(module, descr='there is problem in setting stp config',
                  msg=str(exe))

    existing = None
    try:
        existing = stp.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting existing config.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            stp.build(stage=True, **delta)

    elif state == 'default' or 'absent':
        defaults = stp.get_default_config()
        delta = dict(set(existing.items()).difference(
            defaults.items()))
        if delta:
            stp.default(stage=True)

    commands = None
    # end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                # end_state = stp.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed}
    # results['end_state'] = end_state

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
