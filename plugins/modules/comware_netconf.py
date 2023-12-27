#!/usr/bin/python

DOCUMENTATION = """
---

module: comware_netconf
short_description: Manage netconf log and xml function on Comware 7 devices.XML cfg not support enter xml view now,
                   This is not normally done.
version_added: 1.0.0
author: gongqianyu
category: Feature (RW)
notes:
options:
    source:
        description:
            - NETCONF operation source requiring log output.Option 'all' means all source.
        required: False
        type: str
    operation: 
        description:
            - Netconf operation option.If you chose protocol-operation,the opera_type option must be config.
        required: False
        type: str
    opera_type: 
        description:
            - Protocol-operation option.
        required: False
        type: str
    state:
        description:
            - Desired state for the interface configuration
        required: false
        default: present
        type: str
"""

EXAMPLES = """

      - name: netconf config
        h3c_open.comware.comware_netconf:
          source: all
          operation: protocol-operation
          opera_type: action

      - name: delete netconf config
        h3c_open.comware.comware_netconf:
          source: all
          operation: protocol-operation
          opera_type: action
          state: absent
         
"""

from ansible.module_utils.basic import *
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.netconf import Netconf
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import get_device
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import *


def safe_fail(module, **kwargs):
    module.fail_json(**kwargs)


def safe_exit(module, **kwargs):
    module.exit_json(**kwargs)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            source=dict(required=False, choices=['all', 'agent', 'soap', 'web']),
            operation=dict(required=False, choices=['protocol-operation', 'row-operation', 'verbose']),
            opera_type=dict(required=False,
                            choices=['all', 'action', 'config', 'get', 'session', 'set', 'syntax', 'others']),
            soap=dict(required=False, choices=['http', 'https']),
            state=dict(choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )

    device = get_device(module)
    source = module.params['source']
    soap = module.params['soap']
    operation = module.params['operation']
    opera_type = module.params['opera_type']
    state = module.params['state']
    args = dict(source=source, operation=operation, opera_type=opera_type, soap=soap)

    proposed = dict((k, v) for k, v in args.items() if v is not None)

    changed = False

    net_conf = None
    try:
        net_conf = Netconf(device, source, operation, opera_type, soap)
    except PYCW7Error as exe:
        safe_fail(module, msg=str(exe))

    if state == 'present':
        net_conf.build(stage=True)
    elif state == 'absent':
        net_conf.remove(stage=True)

    commands = None

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
                          descr='error during execution')
            changed = True

    results = {'state': state, 'commands': commands, 'changed': changed, 'proposed': proposed}

    safe_exit(module, **results)


if __name__ == "__main__":
    main()
