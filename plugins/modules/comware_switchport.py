#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_switchport
short_description: Manage Layer 2 parameters on switchport interfaces
author: hanyangyang
description:
    - Manage Layer 2 parameters on switchport interfaces
version_added: 1.0.0
category: Feature (RW)
notes:
    - If the interface is configured to be a Layer 3 port, the module
      will fail and ask the user to use the comware_interface module
      to convert it to be a Layer 2 port first.
    - If the interface is a member in a LAG, the module will fail
      telling the user changes hould be made to the LAG interface
    - If VLANs are trying to be assigned that are not yet created on
      the switch, the module will fail asking the user to create
      them first.
    - If state=default, the switchport settings will be defaulted.
      That means it will be set as an access port in VLAN 1.
options:
    name:
        description:
            - Full name of the interface
        required: true
        type: str
    link_type:
        description:
            - Layer 2 mode of the interface
        required: true
        type: str
    pvid:
        description:
            - If link_type is set to trunk this will be used as the native
              native VLAN ID for that trunk. If link_type is set to access
              then this is the VLAN ID of the interface.
        required: false
        type: str
    permitted_vlans:
        description:
            - If mode is set to trunk this will be the complete list/range
              (as a string) of VLANs allowed on that trunk interface.
              E.g. 1-3,5,8-10
              Any VLAN not in the list
              will be removed from the interface.
        required: false
        type: str
    untaggedvlan:
        description: 
            - Assign hybrid port to untagged VLANs
              E.g. 1-3,5,8-10
        required: false
        type: str
    taggedvlan:
        description:
            - Assign hybrid port to tagged VLANs
              E.g. 1-3,5,8-10
        required: false
        type: str
    state:
        description:
            - Desired state of the switchport
        required: false
        default: present
        type: str

"""
EXAMPLES = """

      - name: ensure layer 2
        h3c_open.comware.comware_interface:
          name: HundredGigE1/0/29
          type: bridged
        register: results
        
      - assert:
          that:
            - "results.end_state.type == 'bridged'"

      - name: ensure VLAN 3 exists
        h3c_open.comware.comware_vlan:
          vlanid: 3
          name: VLAN3_TEST
          descr: 'vlan 3 for testing'
          state: present
        register: results

      - assert:
          that:
            - results.end_state.vlanid == '3'
            - results.end_state.name == 'VLAN3_TEST'
            - results.end_state.descr == 'vlan 3 for testing'

      - name: ensure VLAN 5 exists
        h3c_open.comware.comware_vlan:
          vlanid: 5
          name: VLAN5_TEST
          descr: 'vlan 5 for testing'
          state: present
        register: results
        
"""

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.switchport import Switchport
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.vlan import Vlan
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.portchannel import Portchannel
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            link_type=dict(required=True,
                           choices=['access', 'trunk', 'hybrid']),
            pvid=dict(type='str'),
            permitted_vlans=dict(type='str'),
            untaggedvlan=dict(type='str'),
            taggedvlan=dict(type='str'),
            state=dict(choices=['present', 'default', 'absent'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)

    name = module.params['name']
    state = module.params['state']
    changed = False
    if state == 'present':
        if module.params.get('link_type') == 'access':
            if module.params.get('permitted_vlans') or module.params.get('taggedvlan') or module.params.get(
                    'untaggedvlan'):
                safe_fail(module,
                          msg='Access interfaces don\'t take'
                              + ' permitted vlan lists, untaggedvlan or taggedvlan .')
        elif module.params.get('link_type') == 'trunk':
            if module.params.get('untaggedvlan') or module.params.get('taggedvlan'):
                safe_fail(module,
                          msg='Trunk interfaces don\'t take'
                              + 'untaggedvlan or taggedvlan .')
        elif module.params.get('link_type') == 'hybrid':
            if module.params.get('permitted_vlans'):
                safe_fail(module, msg='Hybrid interface don\'t take '
                                      + 'permitted vlan lists.')

    # Make sure vlan exists
    pvid = module.params.get('pvid')
    if pvid and state != 'default':
        try:
            vlan = Vlan(device, pvid)
            if not vlan.get_config():
                safe_fail(module, msg='Vlan {0} does not exist,'.format(pvid)
                                      + ' Use vlan module to create it.')
        except PYCW7Error as exe:
            module.fail_json(msg=str(exe),
                             descr='Error initializing Vlan object'
                                   + ' or getting current vlan config.')

    # Make sure port is not part of port channel
    pc_list = None
    try:
        portchannel = Portchannel(device, '99', 'bridged')
        pc_list = portchannel.get_all_members()
    except PYCW7Error as exe:
        module.fail_json(msg=str(exe),
                         descr='Error getting port channel information.')
    if name in pc_list:
        safe_fail(module, msg='{0} is currently part of a port channel.'.format(name)
                              + ' Changes should be made to the port channel interface.')

    switchport = None
    try:
        switchport = Switchport(device, name)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error initialzing Switchport object.')

    # Make sure interface exists and is ethernet
    if not switchport.interface.iface_exists:
        safe_fail(module, msg='{0} doesn\'t exist on the device.'.format(name))

    # Make sure interface is in bridged mode
    if_info = None
    try:
        if_info = switchport.interface.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting current interface config.')

    if if_info.get('type') != 'bridged':
        safe_fail(module, msg='{0} is not in bridged mode.'.format(name)
                              + ' Please use the interface module to change that.')

    existing = None
    try:
        existing = switchport.get_config()
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe),
                  descr='Error getting switchpot config.')

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if state == 'present':
        delta = dict(set(proposed.items()).difference(
            existing.items()))
        if delta:
            delta['link_type'] = proposed.get('link_type')
            pvid = proposed.get('pvid')
            if pvid:
                delta['pvid'] = pvid

            switchport.build(stage=True, **delta)
    elif state == 'default':
        defaults = switchport.get_default()
        delta = dict(set(existing.items()).difference(
            defaults.items()))
        if delta:
            switchport.default(stage=True)
    elif state == 'absent':
        # options = {'link_type': "module.params.get('link_type')",
        #                   'pvid': "module.params.get('pvid')",
        #                   'permitted_vlans': "module.params.get('permitted_vlans')",
        #                   'untaggedvlan': "module.params.get('untaggedvlan')",
        #                   'taggedvlan': "module.params.get('taggedvlan')"}
        # options = dict((k, v) for k, v in module.params.items()
        #                 if v is not None and k not in filtered_keys)
        defaults = switchport.get_default()
        delta = dict(set(existing.items()).difference(
            defaults.items()))
        if delta:
            if module.params.get('link_type') == 'hybrid':
                switchport.remove_hybrid(stage=True)
            if module.params.get('link_type') == 'trunk':
                switchport.remove_trunk(stage=True)
            if module.params.get('link_type') == 'access':
                switchport.remove_access(stage=True)
    commands = None
    end_state = existing

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            safe_exit(module, changed=True,
                      commands=commands)
        else:
            try:
                device.execute_staged()
                end_state = switchport.get_config()
            except PYCW7Error as exe:
                safe_fail(module, msg=str(exe),
                          descr='Error during command execution.')
            changed = True

    results = {'proposed': proposed, 'existing': existing, 'state': state, 'commands': commands, 'changed': changed,
               'end_state': end_state}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
print('*********************************')
