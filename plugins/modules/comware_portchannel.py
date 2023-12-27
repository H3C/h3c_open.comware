#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_portchannel
short_description: Manage port-channel (LAG) on Comware 7 devices
description:
    - Manage routed and bridged aggregation configurations on Comware 7
      devices.  This includes physical interface configs for LACP.
version_added: 1.0.0
author: wangliang, gongqianyu
category: Feature (RW)

notes:
    - When configuring a LAGG, the members param must be included
    - Members is ALL members - it is ensuring that the members sent
      is the full list of all members.  This means to remove a member
      it just needs to be removed from the members list.
    - When removing a LAGG, members is not required
    - If mode is set to static, lacp_edge and lacp_mode are disregarded
      if those params are set
options:
    group:
        description:
            - Group number to identify the Aggregate interface
        required: true
        type: str
    members:
        description:
            - COMPLETE Interface List that should be in the agg group.
              Full names should be used AND Interface names ARE case
              sensitive. For example, FortyGigE1/0/1 should NOT be written
              as fortygige1/0/1.  This is for safety.
        required: false
        type: list
    mode:
        description:
            - Mode of the Aggregate interface.If you want to Configure the port rate as a condition for selecting the 
              reference port first, require it.
        required: false
        default: dynamic
        choices: ['static', 'dynamic']
        type: str
    type:
        description:
            - Type of the Aggregate interface (L2 or L3)
        required: true
        choices: ['bridged', 'routed']
        type: str
    lacp_mode:
        description:
            - If mode is set to LACP, the type operating mode can be selected.
              This  mode will then be set for all members in the group.
        required: false
        default: active
        choices: ['active', 'passive']
        type: str
    hash_mode:
        description:
            -Hash mode  for the agg group.
             some mode cannot config use netconfig,like 'flexible' and 'per-packet'.
        required: false
        choices: ['destination-ip', 'destination-mac', 'source-ip', 'source-mac']
        type: str
    min_ports:
        description:
            - Minimum number of selected ports for the agg group
        required: false
        type: str
    max_ports:
        description:
            - Maximum number of selected ports for the agg group
        required: false
        type: str
    lacp_edge:
        description:
            - Determine if an LACP agg group should be an edge aggregate
              interface
        required: false
        choices: ['enabled', 'disabled']
        type: str
    s_mlag:
        description:
            - Determine if add agg group into s_mlag group.If you want to collocate lacp system-mac,
              you must require it
        required: false
        type: str
    speed:
        description:
            - Configure the port rate as a condition for selecting the reference port first.The default state is port ID
               as a condition for selecting the reference port first.Before configure it, the agg group interface must 
               be dynamic agg interface.
        required: false
        choices: ['enabled', 'disabled']
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent']
        type: str

"""

EXAMPLES = """

- name: Ensure ragg 100 does not exist
  h3c_open.comware.comware_portchannel:
    group: 100
    type: routed
    state: absent
  register: data

- name: Config 1
  h3c_open.comware.comware_portchannel:
    group: 100
    members:
      - HundredGigE1/0/27
      - HundredGigE1/0/28
      - HundredGigE1/0/29
      - HundredGigE1/0/30
    type: routed
    mode: static
    min_ports: 2
    max_ports: 4
    state: present
  register: data

- name: Config 2
  h3c_open.comware.comware_portchannel:
    group: 100
    members:
      - HundredGigE1/0/27
      - HundredGigE1/0/28
    type: routed
    mode: dynamic
    lacp_mode: active
    lacp_edge: enabled
    min_ports: 2
    max_ports: 4
    state: present
  register: data

- name: Config 3 - idempotent check
  h3c_open.comware.comware_portchannel:
    group: 100
    members:
      - HundredGigE1/0/27
      - HundredGigE1/0/28
    type: routed
    mode: dynamic
    lacp_mode: active
    lacp_edge: enabled
    min_ports: 2
    max_ports: 4
    state: present
  register: data

- name: Config 4 - removal
  h3c_open.comware.comware_portchannel:
    group: 100
    type: routed
    state: absent
  register: data

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.portchannel import Portchannel
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import (
    InvalidPortType, AggregationGroupError,
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


def get_delta(existing, proposed, existing_members, proposed_members,
              lacp_mode, portchannel):
    portchannel.members_to_remove = list(set(existing_members).difference(
        proposed_members))

    members_to_add = list(set(proposed_members).difference(
        existing_members))

    lacp_modes_by_interface = []
    if 'lacp_modes_by_interface' in existing.keys():
        lacp_modes_by_interface = existing.pop('lacp_modes_by_interface')

    attr_delta = dict(set(proposed.items()).difference(
        existing.items()))

    if members_to_add:
        attr_delta['members'] = members_to_add

    lacp_to_change = []

    for each in lacp_modes_by_interface:
        if each.get('lacp_mode') != lacp_mode \
                and each.get('mode') == 'dynamic':
            lacp_to_change.append(each.get('interface'))

    if lacp_to_change:
        attr_delta['lacp_to_change'] = lacp_to_change
        portchannel.desired_lacp_mode = attr_delta.pop('lacp_mode')
    if 'lacp_mode' in attr_delta.keys():
        attr_delta.pop('lacp_mode')

    return attr_delta


def main():
    module = AnsibleModule(
        argument_spec=dict(
            group=dict(required=True, type='str'),
            members=dict(required=False, type='list'),
            mode=dict(required=False, choices=['static', 'dynamic'], type='str'),
            type=dict(required=True, choices=['bridged', 'routed'], type='str'),
            lacp_mode=dict(required=False, choices=['active', 'passive'], type='str'),
            hash_mode=dict(required=False, choices=['destination-ip', 'destination-mac', 'source-ip', 'source-mac'],
                           type='str'),
            lacp_edge=dict(required=False, choices=['enabled', 'disabled'], type='str'),
            s_mlag=dict(required=False, type='str'),
            speed=dict(required=False, choices=['enabled', 'disabled'], type='str'),
            min_ports=dict(required=False, type='str'),
            max_ports=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)

    groupid = module.params['group']
    members = module.params['members']
    lacp_mode = module.params['lacp_mode']
    hash_mode = module.params['hash_mode']
    mode = module.params['mode']
    lacp_edge = module.params['lacp_edge']
    min_ports = module.params['min_ports']
    max_ports = module.params['max_ports']
    s_mlag = module.params['s_mlag']
    speed = module.params['speed']

    pc_type = module.params['type']

    state = module.params['state']

    if members:
        if not isinstance(members, list):
            module.fail_json(msg='members param must be a list.  YAML format '
                                 + '\nmust be used within the playbook')
    if state == 'present' and not members:
        module.fail_json(msg='members param required when state=present')

    if mode == 'static' and lacp_mode:
        lacp_mode = None
        lacp_edge = None

    changed = False

    args = dict(groupid=groupid, lacp_edge=lacp_edge, mode=mode, hash_mode=hash_mode, s_mlag=s_mlag, speed=speed,
                min_ports=min_ports, max_ports=max_ports, lacp_mode=lacp_mode)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    existing = []
    portchannel = None
    try:
        portchannel = Portchannel(device, groupid, pc_type)
        #       portchannel.param_check(members=members, **proposed)
        existing = portchannel.get_config()
    except InvalidPortType as ipte:
        module.fail_json(msg=str(ipte))
    except AggregationGroupError as age:
        module.fail_json(msg=str(age))
    except PYCW7Error as e:
        module.fail_json(msg=str(e))

    if 'members' in existing.keys():
        # noinspection PyTypeChecker
        existing_members = existing.pop('members')
    else:
        existing_members = []

    if state == 'present':
        delta = get_delta(existing, proposed, existing_members,
                          members, lacp_mode, portchannel)
        if delta:
            # delta['groupid'] = groupid
            portchannel.build(stage=True, **delta)
    elif state == 'absent':
        if existing:
            portchannel.remove(stage=True)

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
                end_state = portchannel.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='error during execution')
            changed = True

    proposed['members'] = members
    proposed['type'] = pc_type

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
