#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_lldp
short_description: Manage lacp fast-Interval, tx-interval,hold-multplier on Comware 7 devices
author: gongqianyu
description:
    - the default fast Interval is 1 and tx-interval is 30,hold-multplier is 4.Using this module ,\
      you must be use comware_lldp_global to enable global

version_added: 1.0.0
category: Feature (RW)
options:
    fast_intervalId:
        description:
            - lldp fast Interval
        required: false
        type: str
    tx_intervalId:
        description:
            - lldp fast Interval
        required: false
        type: str
    multiplierlId:
        description:
            - lldp hold-muliplierlid
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: true
        default: present
        choices: ['present', 'default']
        type: str
"""

EXAMPLES = """

- name: Config lldp
  h3c_open.comware.comware_lldp:
    fast_intervalId: 8
    tx_intervalId: 4
    multiplierId: 8
    state: present
  register: results

- name: Config fast-Interval and tx-interval into default state
  h3c_open.comware.comware_lldp:
    fast_intervalId: 5
    tx_intervalId: 4
    state: default
  register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.lldp import Lldp


def main():
    module = AnsibleModule(
        argument_spec=dict(
            fast_intervalId=dict(required=False, type='str'),
            tx_intervalId=dict(required=False, type='str'),
            multiplierId=dict(required=False, type='str'),
            state=dict(choices=['present', 'default'], default=None),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    fast_intervalId = module.params['fast_intervalId']
    tx_intervalId = module.params['tx_intervalId']
    multiplierId = module.params['multiplierId']
    state = module.params['state']

    changed = False

    args = dict(fast_intervalId=fast_intervalId, tx_intervalId=tx_intervalId, multiplierId=multiplierId)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    LLDP = None
    try:
        LLDP = Lldp(device, module, fast_intervalId, tx_intervalId, multiplierId, state)
        LLDP.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    existing = []
    try:
        existing = LLDP.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error getting priority config')

    LLdp = None
    try:
        LLdp = Lldp(device, module=module)
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='Error initialzing Switchport object.')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            LLdp.build(state=state, stage=True, **delta)

    elif state == 'default':
        LLdp.default(state=state, stage=True)

    commands = None
    end_state = existing

    try:
        device.execute_staged()
        end_state = LLdp.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e),
                         descr='error during execution')

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
