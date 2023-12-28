#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_vlan
short_description: Manage VLAN attributes for Comware 7 devices
description:
    - Manage VLAN attributes for Comware 7 devices
version_added: 1.0.0
author: liudongxue(@liudongxue)
options:
    vlanid:
        description:
            - VLAN ID to configure
            - eg:vlanid=30-40 or vlanid=30
        required: true
        type: str
    name:
        description:
            - Name to configure for the specified VLAN ID
        required: false
        type: str
    descr:
        description:
            - Description for the VLAN
        required: false
        type: str
    state:
        description:
            - Desired state of the vlan
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
"""
EXAMPLES = """

  - name: Ensure VLAN 10 exists
    h3c_open.comware.comware_vlan:
      vlanid: 10
      name: VLAN10_WEB
      descr: LOCALSEGMENT
      state: present
    register: results

  - name: Ensure VLAN 10 exists
    h3c_open.comware.comware_vlan:
      vlanid: 10
      name: VLAN10_WEB
      descr: LOCALSEGMENT
      state: present
    register: results

  - name: Ensure VLAN 10 does not exist
    h3c_open.comware.comware_vlan:
      vlanid: 10
      state: absent
    register: results

  - name: Re-configure VLAN 10
    h3c_open.comware.comware_vlan:
      vlanid: 10
      name: VLAN10_WEB
      state: present
    register: results

"""
import re
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vlan import Vlan
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    LengthOfStringError, VlanIDError
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            vlanid=dict(required=True, type='str'),
            name=dict(required=False, type='str'),
            descr=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent'], default='present')
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    vlanid = module.params['vlanid']
    name = module.params['name']
    descr = module.params['descr']
    state = module.params['state']
    changed = False
    descr_a = module.params['descr']
    name_a = module.params['name']

    vlanidlist = []
    digs = []
    vlan = None
    existing = []
    proposed = dict()
    if re.search(r'(\d+)-(\d+)', vlanid, re.I) is not None:
        t = re.search(r'(\d+)-(\d+)', vlanid, re.I)
        vlanidlist.append(int(t.group(1)))
        vlanidlist.append(int(t.group(2)))
        f = vlanidlist
        for vlanid in range(f[0], f[1] + 1):
            vlanid = str(vlanid)
            dig = re.compile(r'\d+')
            if name_a is not None:
                digs = dig.findall(name)
            args = dict(vlanid=vlanid, name=name, descr=descr)
            if digs:
                digs = int(digs[0]) + 1
                name = re.sub(r'\d+', str(digs), name)
            elif digs == [] and name_a is not None:
                num = int(vlanid) + 1
                name = name_a + str(num)
            if descr is not None:
                num = int(vlanid) + 1
                descr = descr_a + "_" + str(num)
            proposed = dict((k, v) for k, v in args.items() if v is not None)
            try:
                vlan = Vlan(device, vlanid)
                vlan.param_check(**proposed)
            except LengthOfStringError as lose:
                module.fail_json(msg=str(lose))
            except VlanIDError as vie:
                module.fail_json(msg=str(vie))
            except PYCW7Error as e:
                module.fail_json(msg=str(e))

            try:
                existing = vlan.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error getting vlan config')

            if state == 'present':
                delta = dict(set(proposed.items()).difference(
                    existing.items()))
                if delta:
                    vlan.build(stage=True, **delta)
            elif state == 'absent':
                if existing:
                    vlan.remove(stage=True)
    else:
        args = dict(vlanid=vlanid, name=name, descr=descr)
        proposed = dict((k, v) for k, v in args.items() if v is not None)

        try:
            vlan = Vlan(device, vlanid)
            vlan.param_check(**proposed)
        except LengthOfStringError as lose:
            module.fail_json(msg=str(lose))
        except VlanIDError as vie:
            module.fail_json(msg=str(vie))
        except PYCW7Error as e:
            module.fail_json(msg=str(e))

        try:
            existing = vlan.get_config()
        except PYCW7Error as e:
            module.fail_json(msg=str(e),
                             descr='error getting vlan config')
        if state == 'present':
            delta = dict(set(proposed.items()).difference(
                existing.items()))
            if delta:
                vlan.build(stage=True, **delta)
        elif state == 'absent':
            if existing:
                vlan.remove(stage=True)
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
                end_state = vlan.get_config()
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
