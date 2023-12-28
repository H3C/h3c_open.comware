#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_acl
short_description: Configure the acl issue to be applied to the interface.
description:
    - Configure the acl issue to be applied to the interface.
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - When using this feature, "acliid" and "groupcg" are required parameters.
    - You must select a groupcategory when configurating the acl.
    - If you want to configure rule,you need to configure the acl first.
      The rule value range 0 to 65535.The value 65535 is an invalid rule ID.
      If you want to configure acl advanded,the acl id rang from 3000 to 3999.
    - If you want to configure acl basic,the acl id rang from 2000 to 2999.
    - When you want to create an rule, you must have a "aclid" and "action" and "scripaddr".
    - When you want to apply an rule to the interface, you must configure "aclid" and "groupcg".
    - You cannot have a "groupcg" parameter when deleting a rule.

options:
    aclid:
        description:
            - The ID of ACL
        required: true
        type: str
    name:
        description:
            - Full name of the interface
        required: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        choices: ['present', 'absent']
        default: present
        type: str
    ruleid:
        description:
            - The ID of rule
        required: false
        type: str
    scripaddr:
        description:
            -  Ip source address of rule
        required: false
        type: str
    action:
        description:
            - Action of the rule
        required: false
        choices: ['deny', 'permit']
        type: str
    appdirec:
        description:
            - Direction Applied to the interface
        required: false
        choices: ['inbound', 'outbound']
        type: str
    groupcg:
        description:
            - ACL groupacategory
        required: false
        choices: ['basic', 'advanced']
        type: str

"""
EXAMPLES = """
      - name: deploy advanced ACL (IPv4 advanced ACL 3000 to 3999)
        h3c_open.comware.comware_acl:
          aclid: 3010
          groupcg: advanced


      - name: deploy basic ACL (IPv4 basic ACL 2000 to 2999)
        h3c_open.comware.comware_acl:
          aclid: 2010
          groupcg: basic

      - name: delete advanced ACL
        h3c_open.comware.comware_acl:
          aclid: 3010
          groupcg: advanced
          state: absent
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.acl import Acl


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            aclid=dict(type='str', required=True),
            name=dict(required=False),
            state=dict(choices=['present', 'absent'],
                       default='present'),
            ruleid=dict(type='str'),
            scripaddr=dict(type='str'),
            action=dict(choices=['deny', 'permit']),
            appdirec=dict(choices=['inbound', 'outbound']),
            groupcg=dict(choices=['basic', 'advanced']),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    state = module.params['state']
    # name = module.params['name']
    aclid = str(module.params['aclid'])
    ruleid = module.params['ruleid']
    scripaddr = module.params['scripaddr']
    action = str(module.params['action'])
    # appdirec = module.params['appdirec']
    changed = False

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None)

    if module.params.get('appdirec'):
        if not module.params.get('name'):
            safe_fail(module, msg='appdirec needs to be provided with name')

    if module.params.get('name'):
        name = module.params.get('name')
        try:
            interface = Interface(device, name)
        except PYCW7Error as exe:
            safe_fail(module,
                      descr='There was problem recognizing that interface.',
                      msg=str(exe))
        if not module.params.get('aclid') or not module.params.get('appdirec'):
            module.fail_json(msg='The type parameter must be compatible with:'
                                 '\naclid, appdirec.'
                                 '\nPlease configure type first by itself,'
                                 '\nthen run again.')
    else:
        name = ''
        try:
            interface = Interface(device, name)
        except PYCW7Error as exe:
            safe_fail(module,
                      descr='There was problem recognizing that interface.',
                      msg=str(exe))
    if state == 'present':
        if module.params.get('ruleid'):
            ruleid = module.params.get('ruleid')
            if not module.params.get('aclid') or not module.params.get('action') \
                    or not module.params.get('scripaddr'):
                module.fail_json(msg='The type parameter must be compatible with:'
                                     '\naclid, action, scripaddr.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
        else:
            ruleid = None

    if not module.params.get('aclid'):
        module.fail_json(msg='The type parameter must be set'
                             '\nPlease configure type first by itself,'
                             '\nthen run again.')
    if not module.params.get('scripaddr'):
        scripaddr = None

    acl = Acl(device, aclid, name, ruleid, scripaddr)

    if state == 'present':
        if not module.params.get('groupcg'):
            module.fail_json(msg='The type parameter must be compatible with:'
                                 '\ngroupcg.'
                                 '\nPlease configure type first by itself,'
                                 '\nthen run again.')

        else:
            args = dict(groupcg=module.params.get('groupcg'))
            acl.create_acl(stage=True, **args)
            if ruleid:
                acl.create_rule(stage=True, action=action)
                if name != '':
                    arg = dict(appdirec=module.params.get('appdirec'))
                    acl.create_packet_filter(stage=True, **arg)
            if name != '':
                arg = dict(appdirec=module.params.get('appdirec'))
                acl.create_packet_filter(stage=True, **arg)
    else:
        if module.params.get('groupcg'):
            args = dict(groupcg=module.params.get('groupcg'))
            acl.remove_acl(stage=True, **args)
        elif ruleid:
            acl.remove_rule(stage=True)
        if name != '':
            args = dict(appdirec=module.params.get('appdirec'))
            acl.remove_packet_filter(stage=True, **args)
    existing = True
    commands = None
    end_state = True

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
                          descr='Error on device execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
