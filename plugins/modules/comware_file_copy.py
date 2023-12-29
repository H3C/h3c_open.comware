#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2020 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
DOCUMENTATION = """
---

module: comware_file_copy
short_description: Copy a local file to a remote Comware v7 device
description:
    - Copy a local file to a remote Comware v7 device
version_added: 1.0.0
author: liudongxue(@liudongxue)
notes:
    - If the remote directory doesn't exist, it will be automatically
      created.
    - If you want to use FTP, you need to enable the FTP function on the device,
      e.g.
        [Sysname] local-user h3c class manage
        [Sysname-luser-manage-h3c] service-type ftp
        [Sysname] ftp server enable
      You can configure it using the 'comware_local_user.py' and 'comware_ftp.py' modules first.
options:
    file:
        description:
            - File (including absolute path of local file) that will be sent
              to the device
        required: true
        type: str
    remote_path:
        description:
            - Full file path on remote Comware v7 device, e.g. flash:/myfile.
              If no directory is included in remote_path, flash will be prepended.
              If remote_path is omitted, flash will be prepended to the source file name.
        required: false
        type: str
    ftpupload:
        description:
            - If you want to upload by FTP, change the params to true
        required: false
        default: 'false'
        choices: ['true', 'false']
        type: str
    ftpdownload:
        description:
            - If you want to download by FTP, change the params to true
        required: false
        choices: ['true', 'false']
        default: 'false'
        type: str
    hostname:
        description:
            - IP Address or hostname of the Comware v7 device that has
              NETCONF enabled
        required: true
        type: str
    username:
        description:
            - Username used to login to the switch
        required: true
        type: str
    password:
        description:
            - Password used to login to the switch
        required: false
        type: str
"""

EXAMPLES = """

- name: Copy file
  h3c_open.comware.comware_file_copy:
    file: /usr/smallfile
    remote_path: flash:/otherfile

- name: Ftp upload
  h3c_open.comware.comware_file_copy:
    file: /root/ansible_collections.h3c_open.comware.plugins.module_utils.network.comware-ansible-master/vlans.yml
    remote_path: flash:/ldx/vlans.yml
    ftpupload: true

- name: Use FTP to download files to the server--module 1.3
  h3c_open.comware.comware_file_copy:
      file: /root/ansible_collections.h3c_open.comware.plugins.module_utils.network.comware-ansible-master/11.txt
      remote_path: flash:/llld/11.txt
      ftpdownload: true
"""
import socket
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.file_copy import FileCopy
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.comware import (
    get_device
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            file=dict(required=True),
            remote_path=dict(type='str'),
            ftpupload=dict(required=False, type='str', default='false', choices=['true', 'false']),
            ftpdownload=dict(required=False, type='str', default='false', choices=['true', 'false']),
            hostname=dict(required=True, type='str'),
            username=dict(required=True, type='str'),
            password=dict(required=False, type='str', default=None, no_log=True),
        ),
        supports_check_mode=False
    )

    hostname = socket.gethostbyname(module.params['hostname'])
    username = module.params['username']
    password = module.params['password']
    device = get_device(module)
    src = module.params.get('file')
    dst = module.params.get('remote_path')
    ftpupload = module.params.get('ftpupload')
    ftpdownload = module.params.get('ftpdownload')
    changed = False
    file_copy = None
    try:
        file_copy = FileCopy(device, src, dst)
        if ftpdownload == 'false':
            if not file_copy.file_already_exists:
                if not file_copy.remote_dir_exists:
                    file_copy.create_remote_dir()
                if ftpupload == 'true':
                    file_copy.ftp_file(hostname, username, password)
                else:
                    file_copy.transfer_file(hostname, username, password)
                changed = True
        else:
            if file_copy.remote_dir_exists:
                file_copy.ftp_downloadfile()
                changed = True
            else:
                module.fail_json(msg='The remote path not exists , please check it')

    except PYCW7Error as fe:
        module.fail_json(msg=str(fe),
                         descr='Error transferring file.')

    results = {}
    results['source_file'] = file_copy.src
    results['destination_file'] = file_copy.dst
    results['changed'] = changed

    module.exit_json(**results)


if __name__ == "__main__":
    main()
