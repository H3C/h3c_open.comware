#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_log
short_description: get the device diagnostic information and upload to file server
description:
    - get the device diagnostic information and upload to file server
version_added: 1.0.0
author: h3c (@h3c_open)
notes:
    - Getting device diagnostic information will take some time , here give 300s to get the information,
      if result goes to time out , check the timeout 300s first.
    - if state is present , you will get the diag file with .tar.gz , and it will upload to ansible
      server.
options:
    service_dir:
        description:
            - the dir in server which you want to upload the diag file from device
        required: false
        type: str
    diag_dir:
        description:
            - where the device diagnostic information storage , default is flash:/
        required: false
        default: 'flash:/'
        type: str
    ftpupload:
        description:
            - whether upload the diagnostic information to the service.
        required: false
        default: true
        type: bool
    servertype:
        description:
            - choose the diagnostic file upload server type.
        required: false
        choices: ['ftp','scp']
        type: str
    server_hostname:
        description:
            - the remote server hostname e.g.192.168.1.199.
        required: false
        type: str
    server_name:
        description:
            - the name to login in remote server.
        required: false
        type: str
    server_pwd:
        description:
            - the password to login in remote server.
        required: false
        type: str
    dst_dir:
        description:
            - remote dir where the file save.
        required: false
        type: str
    state:
        description:
            - The state of operation
        required: false
        choices: ['present', 'default', 'loadtoserver']
        default: present
        type: str
"""
EXAMPLES = """
- name: get diagnostic information to the file server(local)
  h3c_open.comware.comware_log:
    diag_dir: flash:/diaglog
    service_dir: /home/root/ftp/files
    ftpupload: true
    server_name: "{{ ansible_user }}"
    server_pwd: "{{ ansible_password }}"
    server_hostname: "{{ ansible_host }}"

- name: upload diagnostic information to server by scp
  h3c_open.comware.comware_log:
    state: loadtoserver
    servertype: ftp
    server_name: "{{ ansible_user }}"
    server_pwd: "{{ ansible_password }}"
    server_hostname: "{{ ansible_host }}"
    diag_dir: flash:/diaglog
    service_dir: /home/root/ftp/files
    dst_dir: flash:/
- name: upload diagnostic information to server by scp
  h3c_open.comware.comware_log:
    state: loadtoserver
    servertype: scp
    server_name: "{{ ansible_user }}"
    server_pwd: "{{ ansible_password }}"
    server_hostname: "{{ ansible_host }}"
    diag_dir: flash:/diaglog
    service_dir: /home/root/ftp/files
    dst_dir: flash:/
- name: delete diagnostic information in device
  h3c_open.comware.comware_log:
    diag_dir: flash:/diaglog
    state: default
"""

import re
import time
import traceback
from ansible.module_utils.basic import missing_required_lib

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file_copy import FileCopy

try:
    import paramiko

    HAS_PARAMIKO = True
    PARAMIKO_IMPORT_ERROR = None
except ImportError:
    HAS_PARAMIKO = False
    PARAMIKO_IMPORT_ERROR = traceback.format_exc()

try:
    from scp import SCPClient

    HAS_SCP = True
    SCP_IMPORT_ERROR = None
except ImportError:
    HAS_SCP = False
    SCP_IMPORT_ERROR = traceback.format_exc()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            service_dir=dict(type='str'),
            diag_dir=dict(type='str', default='flash:/'),
            ftpupload=dict(required=False, type='bool', default=True),
            servertype=dict(required=False, choices=['ftp', 'scp']),
            server_hostname=dict(type='str'),
            server_name=dict(type='str'),
            server_pwd=dict(type='str'),
            dst_dir=dict(type='str'),
            state=dict(choices=['present', 'default', 'loadtoserver'],
                       default='present'),
        ),
        supports_check_mode=True
    )

    filtered_keys = ('state', 'hostname', 'username', 'password',
                     'port', 'CHECKMODE', 'name', 'look_for_keys')

    device = get_device(module)
    state = module.params['state']
    diag_dir = module.params['diag_dir']
    service_dir = module.params.get('service_dir')
    ftpupload = module.params.get('ftpupload')
    server_hostname = module.params.get('server_hostname')
    server_name = module.params.get('server_name')
    server_pwd = module.params.get('server_pwd')
    dst_dir = module.params.get('dst_dir')
    changed = False
    proposed = dict((k, v) for k, v in module.params.items()
                    if v is not None and k not in filtered_keys)

    if module.params.get('diag_dir'):
        res = re.search(r'^flash:/', diag_dir)
        if not res:
            module.fail_json(msg='please check diagnose dir ')
        res1 = re.search(r'/$', diag_dir)
        if not res1:
            diag_dir = diag_dir + '/'

    if module.params.get('service_dir'):
        res2 = re.search(r'/$', service_dir)
        if not res2:
            service_dir = service_dir + '/'

    if module.params.get('state') == 'loadtoserver':
        if not module.params.get('servertype'):
            module.fail_json(msg='please choose server type to upload log')

    if state == 'present':
        timenow = time.localtime()
        timeinfo = (str(timenow.tm_year) + str(timenow.tm_mon).zfill(2) + str(timenow.tm_mday).zfill(2) +
                    str(timenow.tm_hour).zfill(2) + str(timenow.tm_min).zfill(2) + str(timenow.tm_sec).zfill(2))
        log_file_name = 'diag_H3C_' + timeinfo + '.tar.gz'
        src = service_dir + log_file_name
        dst = diag_dir + log_file_name
        file_copy = FileCopy(device, src, dst)
        if not file_copy.remote_dir_exists:
            file_copy.create_remote_dir()
            cmd = ['dis diagnostic-information ' + diag_dir + log_file_name]
        else:
            cmd = ['dis diagnostic-information ' + diag_dir + log_file_name]
        device.cli_display(cmd)
        command = ['dir' + ' ' + diag_dir]
        diaglog = device.cli_display(command)
        changed = True
        regex = re.compile(r'diag.*.tar.gz')
        existlog = regex.findall(diaglog)
        # download diaglog to service dir
        if module.params.get('service_dir'):
            if log_file_name in existlog:
                diag_name = existlog[-1]
                file = diag_dir + diag_name
                service_file = service_dir + diag_name
                if ftpupload:
                    if not HAS_PARAMIKO:
                        module.fail_json(
                            msg=missing_required_lib('paramiko'),
                            exception=PARAMIKO_IMPORT_ERROR)
                    if not HAS_SCP:
                        module.fail_json(
                            msg=missing_required_lib('scp'),
                            exception=SCP_IMPORT_ERROR)
                    ssh = paramiko.SSHClient()
                    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                    ssh.connect(hostname=server_hostname,
                                username=server_name,
                                password=server_pwd,
                                port=22,
                                allow_agent=False,
                                look_for_keys=False)
                    scp = SCPClient(ssh.get_transport())
                    scp.get(file, service_file)
                    changed = True
            else:
                module.fail_json(msg='can not get diagnostic information , please check the diag dir ')

    elif state == 'loadtoserver':
        command = ['dir' + ' ' + diag_dir]
        diaglog = device.cli_display(command)
        regex = re.compile(r'diag.*.tar.gz')
        existlog = regex.findall(diaglog)
        if not existlog:
            module.fail_json(msg='can not find file')
        src = service_dir + existlog[-1]
        dst = dst_dir + existlog[-1]
        if src:
            if module.params.get('servertype') == 'ftp':
                server_ftp = FileCopy(device, src, dst)
                server_ftp.ftp_file(hostname=server_hostname,
                                    username=server_name,
                                    password=server_pwd)
                changed = True
            if module.params.get('servertype') == 'scp':
                server_scp = FileCopy(device, src, dst)
                server_scp.transfer_file(hostname=server_hostname,
                                         username=server_name,
                                         password=server_pwd)
                changed = True

    elif state == 'default':
        cmd = ['delete /unreserved' + ' ' + diag_dir + 'diag*.tar.gz']
        device.cli_display(cmd)
        changed = True

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
                                 descr='Error on device execution.')
            changed = True

    results = {}
    results['proposed'] = proposed
    results['commands'] = commands
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
