#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_evpn
short_description: Configure the EVPN issue to be applied to the device.
description:
    -Configure the EVPN issue to be applied to the device.
version_added: 1.0.0
category: Feature (RW)
author: liudongxue
notes:
    - The asnum is unsigned integer,and the value range is 1 to 4294967295.
    - The type of vrf is string,the length is 1 to 31 characters.
    - The type of mask is Unsigned integer,and the value range is 0 to 128,or 255.
      For non-dynamic peers, this is 255.For IPv4 dynamic peers,this is 0 to 32.For IPv6 dynamic peers, \
      this is 0 to 128. 
      Dynamic peers are not supported.
    - if you want to config bgp  evpn   ,please use comware_bgp_global.py to create bgp process first.

options:
    name:
        description:
            - Full name of the interface
        required: false
        type: str
    vrf:
        description:
            - VPN instance name.
        required: false
        default: false
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        choices: ['present', 'absent']
        type: str
    rd:
        description:
            - Route distinguisher
        required: false
        default: false
        type: str
    rtentry:
        description:
            - Route target
        required: false
        type: str
    addrfamily:
        description:
            - Address family
        required: false
        choices: ['ipv4', 'ipv6', 'vpn', 'evpn']
        type: str
    rttype:
        description:
            - RT type
        required: false
        choices: ['import', 'export']
        type: str
    asnum:
        description:
            - Autonomous System number
        required: false
        choices: ['md5', 'hmac_sha_1', 'hmac_sha_256', 'hmac_sha_384', 'hmac_sha_384']
        type: str
    sessaf:
        description:
            - Address family of session
        required: false
        choices: ['ipv4', 'ipv6']
        type: str
    ipaddr:
        description:
            - Remote IPv4 or IPv6 address
        required: false
        type: str
    mask:
        description:
            - Mask of session address
        required: false
        type: str
    aftype:
        description:
            - Address Family Identifier
        required: false
        choices: ['ipv4uni','ipv4mul','mdt', 'vpnv4','ipv6uni','ipv6mul', 'vpnv6','l2vpn','l2vpn_evpn','link_state', 
                  'ipv4mvpn','ipv4flosp', 'vpnv4flosp', 'ipv6flosp', 'vpnv6flosp']
        type: str
    family:
        description:
            - Address Family Identifier of Neighbor
        required: false
        choices: ['ipv4uni','ipv4mul','mdt', 'vpnv4','ipv6uni','ipv6mul', 'vpnv6','l2vpn','l2vpn_evpn','link_state', 
                  'ipv4mvpn','ipv4flosp', 'vpnv4flosp', 'ipv6flosp', 'vpnv6flosp']
        type: str
    del_bgp:
        description:
            - Whether delete BGP
        required: false
        type: bool
"""
EXAMPLES = """

- name: Configure evpn rd
  h3c_open.comware.comware_evpn:
    vrf: 100
    rd: '2:1'
  register: results

- name: Delete evpn rd
  h3c_open.comware.comware_evpn:
    vrf: 100
    state: absent
  register: results

- name: Configure evpn rt
  h3c_open.comware.comware_evpn:
    vrf: ali1
    addrfamily: ipv4
    rttype: export
    rtentry: '30:2'
  register: results

- name: Delete evpn rt
  h3c_open.comware.comware_evpn:
    vrf: ali1
    addrfamily: ipv4
    rttype: export
    rtentry: '30:2'
    state: absent
  register: results

- name: Create bgp ipv6
  h3c_open.comware.comware_evpn:
    bgp_name: 10
    vrf: 200
    asnum: 120
    mask: 128
    ipaddr: 1:1::1:1
    sessaf: ipv6
    state: present
  register: results

- name: Create bgp 100
  h3c_open.comware.comware_evpn:
    bgp_name: 100
    asnum: 130
    state: present
  register: results

- name: Delete bgp
  h3c_open.comware.comware_evpn:
    del_bgp: true
    state: absent
  register: results
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.evpn import Evpn, EVPN
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.interface import Interface


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=False, type='str'),
            state=dict(choices=['present', 'absent'],
                       default='present'),
            vrf=dict(type='str'),
            rd=dict(type='str'),
            rtentry=dict(type='str'),
            addrfamily=dict(choices=['ipv4', 'ipv6', 'vpn', 'evpn'], type='str'),
            rttype=dict(choices=['import', 'export'], type='str'),
            bgp_name=dict(type='str'),
            asnum=dict(type='str'),
            sessaf=dict(choices=['ipv4', 'ipv6'], type='str'),
            ipaddr=dict(type='str'),
            mask=dict(type='str'),
            aftype=dict(
                choices=['ipv4uni', 'ipv4mul', 'mdt', 'vpnv4', 'ipv6uni', 'ipv6mul', 'vpnv6', 'l2vpn', 'l2vpn_evpn',
                         'link_state', 'ipv4mvpn', 'ipv4flosp', 'vpnv4flosp', 'ipv6flosp', 'vpnv6flosp'],
                type='str'),
            family=dict(
                choices=['ipv4uni', 'ipv4mul', 'mdt', 'vpnv4', 'ipv6uni', 'ipv6mul', 'vpnv6', 'l2vpn', 'l2vpn_evpn',
                         'link_state', 'ipv4mvpn', 'ipv4flosp', 'vpnv4flosp', 'ipv6flosp', 'vpnv6flosp'],
                type='str'),
            del_bgp=dict(choices=['true', 'false']),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)

    state = module.params['state']
    name = module.params['name']
    vrf = str(module.params['vrf'])
    rd = module.params['rd']
    rtentry = module.params['rtentry']
    bgp_name = module.params['bgp_name']
    addrfamily = module.params['addrfamily']
    rttype = str(module.params['rttype'])
    asnum = module.params['asnum']
    sessaf = module.params['sessaf']
    ipaddr = module.params['ipaddr']
    mask = str(module.params['mask'])
    aftype = module.params['aftype']
    family = module.params['family']
    del_bgp = module.params['del_bgp']
    changed = False

    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if module.params.get('mask'):
        if sessaf == 'ipv4':
            if int(mask) > 32:
                module.fail_json(msg='IPv4 address mask length is out of range')
        elif sessaf == 'ipv6':
            if int(mask) > 128:
                module.fail_json(msg='IPv6 address mask length is out of range')

    interface = None
    name_exist = False
    if module.params.get('name'):
        name = module.params.get('name')
        try:
            interface = Interface(device, name)
            name_exist = True
        except PYCW7Error as e:
            module.fail_json(descr='There was problem recognizing that interface.',
                             msg=str(e))
        if name_exist:
            is_ethernet, is_routed = interface._is_ethernet_is_routed()
            if is_ethernet:
                module.fail_json(msg='The interface mode must be routing.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
    else:
        name = ''
        try:
            interface = Interface(device, name)
        except PYCW7Error as e:
            module.fail_json(descr='There was problem recognizing that interface.',
                             msg=str(e))
    if state == 'present':
        if module.params.get('rd'):
            if not module.params.get('vrf'):
                module.fail_json(msg='The \'rd\' parameter must be compatible with:'
                                     '\nvrf.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
        if module.params.get('addrfamily'):
            if not module.params.get('vrf') or not module.params.get('rttype') \
                    or not module.params.get('rtentry'):
                module.fail_json(msg='The \'addrfamily\' parameter must be compatible with:'
                                     '\nvrf, rttype, rtentry.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
        if module.params.get('family'):
            if not module.params.get('sessaf') or not module.params.get('ipaddr') \
                    or not module.params.get('mask'):
                module.fail_json(msg='The \'family\' parameter must be compatible with:'
                                     '\nsessaf, ipaddr, mask.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
    if state == 'absent':
        if module.params.get('addrfamily'):
            if not module.params.get('vrf') or not module.params.get('rttype') \
                    or not module.params.get('rtentry'):
                module.fail_json(msg='The \'addrfamily\' parameter must be compatible with:'
                                     '\nvrf, rttype,rtentry,when you want to delete the configurations.'
                                     '\nPlease configure type first by itself,'
                                     '\nthen run again.')
    evpn = Evpn(device, name)
    if state == 'present':
        if module.params.get('rd'):
            evpn.create_evpn(stage=True, vrf=vrf, rd=rd)
        if module.params.get('addrfamily'):
            args = dict(addrfamily=str(module.params.get('addrfamily')), rttype=str(module.params.get('rttype')))
            evpn.comfigue_evpn_rt(stage=True, vrf=vrf, rtentry=rtentry, **args)
        if module.params.get('asnum') and not module.params.get('sessaf'):
            evpn.create_bgp_instance(stage=True, asnum=asnum)
        if module.params.get('asnum') and module.params.get('sessaf'):
            EVpn = EVPN(device, asnum, bgp_name, ipaddr, mask, vrf)
            EVpn.build(stage=True)
        if module.params.get('aftype') and module.params.get('family'):
            arg = dict(aftype=module.params.get('aftype'))
            evpn.entry_bgp_view(stage=True, **arg)
            args = dict(family=str(module.params.get('family')), sessaf=str(module.params.get('sessaf')))
            evpn.publish_bgp_route(stage=True, ipaddr=ipaddr, mask=mask, **args)
    if state == 'absent':
        if module.params.get('vrf') and not module.params.get('addrfamily'):
            evpn.remove_evpn_rd(stage=True, vrf=vrf)
        if module.params.get('addrfamily'):
            args = dict(addrfamily=str(module.params.get('addrfamily')), rttype=str(module.params.get('rttype')))
            evpn.remove_evpn_rt(stage=True, vrf=vrf, rtentry=rtentry, **args)
        if del_bgp == 'true':
            evpn.remove_bgp_instance(stage=True)
    existing = True
    commands = None
    end_state = True

    if device.staged:
        commands = device.staged_to_string()
        if module.check_mode:
            module.exit_json(changed=True,
                             commands=commands)
        else:
            try:
                device.execute_staged()
                # end_state = interface.get_config()
            except PYCW7Error as e:
                module.fail_json(msg=str(e),
                                 descr='Error on device execution.')
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
