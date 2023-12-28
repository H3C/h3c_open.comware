#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_isis_interface
short_description: Manage isis for Comware 7 devices
description:
    - Manage isis for Comware 7 devices
author: gongqianyu(@gongqianyu)
version_added: 1.0.0
options:
    name:
        description:
            - interface name
        required: true
        type: str
    isisID:
        description:
            - Specifies that IS-IS functions are enabled on the interface and configures the IS-IS \
               processes associated with the interface
        required: true
        type: str
    level:
        description:
            - Link adjacency type of configuration interface.
        required: false
        choices: ['level-1', 'level-2', 'level-1-2']
        type: str
    networkType:
        description:
            - Configure the network type of IS-IS interface
        required: false
        choices: ['p2p']
        type: str
    cost:
        description:
            - Configure the link cost value of IS-IS interface.(1～16777215)
        required: false
        type: int
    routerid:
        description:
            - Configure the link cost value of IS-IS interface,to chose router.
        required: false
        choices: ['level-1', 'level-2']
        type: str
    silent:
        description:
            - Forbid the interface to send and receive IS-IS message.
        required: false
        type: bool
    state:
        description:
            - Desired state of the vlan
        required: false
        default: present
        choices: ['present', 'absent']
        type: str

"""
EXAMPLES = """

  - name: create isis 4 and releated params.
    h3c_open.comware.comware_isis_interface:
      name: vlan-interface1
      isisID: 4
      level: level-2
      networkType: p2p
      cost: 5
      routerid: level-2
      silent: true
      state: present
    register: results

  - name: delete isis 4
    h3c_open.comware.comware_isis_interface:
      name: vlan-interface1
      isisID: 4
      level: level-2
      networkType: p2p
      cost: 5
      routerid: level-2
      silent: true
      state: absent
    register: results

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.isis_interface import Isis
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.isis_interface import ISis
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            # enable=dict(required=False),
            isisID=dict(required=True, type='str'),
            level=dict(required=False, choices=['level-1', 'level-2', 'level-1-2'], type='str'),
            networkType=dict(required=False, choices=['p2p'], type='str'),
            cost=dict(required=False, type='int'),
            routerid=dict(required=False, choices=['level-1', 'level-2'], type='str'),
            silent=dict(required=False, type='bool'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    name = module.params['name']
    isisID = module.params['isisID']
    level = module.params['level']
    cost = module.params['cost']
    routerid = module.params['routerid']
    networkType = module.params['networkType']
    silent = module.params['silent']
    state = module.params['state']

    changed = False

    args = dict(name=name, isisID=isisID, level=level, cost=cost, routerid=routerid, networkType=networkType,
                silent=silent)
    proposed = dict((k, v) for k, v in args.items() if v is not None)

    isis = None
    iSis = None
    try:

        isis = Isis(device, name)
        iSis = ISis(device, name, isisID, level, cost, routerid, networkType, silent)
    #     isis.param_check(**proposed)
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    existing = []
    try:
        existing = isis.get_config()
    except PYCW7Error as e:
        module.fail_json(msg=str(e), descr='error getting isis config')

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            if (module.params['cost'] or module.params['routerid'] or module.params['networkType'] or
                    module.params['silent'] or module.params['level']):
                iSis.build(stage=True)
            else:
                isis.build(stage=True, **delta)
    elif state == 'absent':
        if existing:
            iSis.remove(stage=True)

    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            device.close()
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = isis.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e), descr='error during execution')
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
