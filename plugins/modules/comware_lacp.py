#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_lacp
short_description: Manage lacp system priority, system mac on Comware 7 devices
version_added: 1.0.0
author: gongqianyu
category: Feature (RW)
options:
    priorityID:
        description:
            - lacp priority,default is 32768
        required: false
        type: str
    sysmac:
        description:
            - lacp system mac address
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

  - name: lacp config
    h3c_open.comware.comware_lacp:
      priorityID: 8
      sysmac: 2-2-2
      state: present
    register: results

  - name: lacp config
    h3c_open.comware.comware_lacp:
      priorityID: 32768
      state: default
    register: results

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.lacp import Lacp


def main():
    module = AnsibleModule(
        argument_spec=dict(
            priorityID=dict(required=False, type='str'),
            sysmac=dict(required=False, type='str'),
            state=dict(choices=['present', 'default'], default=None),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    priorityID = module.params['priorityID']
    sysmac = module.params['sysmac']
    state = module.params['state']

    changed = False
    args = dict(priorityID=priorityID, sysmac=sysmac)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    LACP = None
    try:
        LACP = Lacp(device, priorityID)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    if state == 'present':

        if module.params.get('priorityID'):
            LACP.build(stage=True)
        if module.params.get('sysmac'):
            LACP.build_time(stage=True, sysmac=sysmac)

    elif state == 'default':

        if module.params.get('priorityID'):
            LACP.remove(stage=True)
        if module.params.get('sysmac'):
            LACP.build_time_absent(stage=True, sysmac=sysmac)

    commands = None

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:

                device.execute_staged()

            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')

            changed = True

    results = {}
    results['proposed'] = proposed
    results['state'] = state
    results['commands'] = commands
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
