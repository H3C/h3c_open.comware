"""Manage file transfer to COM7 devices.
author: liudongxue
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import hashlib
import os
import re
from ftplib import FTP

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import \
    FileNotEnoughSpaceError, \
    FileNotReadableError, FileRemoteDirDoesNotExist, FileTransferError, FileHashMismatchError
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    data_element_maker, find_in_data, action_element_maker, find_in_action)

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False


class FileCopy(object):
    """This class is used to copy local files to a ``COM7`` device.

    Note:
        SCP should first be enabled on the device.

    Note:
        When using this class, the passed in ``COM7`` object should
        be constructed with the ``timeout`` equal to at least 60 seconds.
        Remote MD5 sum calculations can take some time.

    Note:
        If the remote directory doesn't exist (check ``remote_dir_exists``),
        it's the responsibility of the user to call ``create_remote_dir()``
        before calling ``transfer_file()``. Otherwise, a
        ``FileRemoteDirDoesNotExist`` exception will be raised.

    Args:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.
        src (str): Full path to local file to be copied.
        dst (str): OPTIONAL - Full path or filename of remote file.
            If just a filename is supplied, 'flash:/' will be prepended.
            If nothing is supplied, the source filename will be used,
            and 'flash:/' will be prepended.
        port (int): OPTIONAL - The SSH port over which
            the SCP connection is made. Defaults to 22.

    Attributes:
        device (COM7): connected instance of
            a ``comware.comware.COM7`` object.
        src (str): Full path to local file to be copied.
        dst (str): Full path of remote file.
        port (int): The SSH port over which
            the SCP connection is made.
        remote_dir_exists (bool): Whether there remote
            directory exists.
    """

    def __init__(self, device, src, dst=None, port=22):
        self.device = device
        self.src = src
        self.dst = dst or os.path.basename(src)

        if self.dst.find(':/') < 0:
            self._remote_dir = 'flash:/'
            self.dst = self._remote_dir + self.dst
            self.ftp_dst = os.path.basename(self.src)
        else:
            self._remote_dir = '/'.join(
                self.dst.split('/')[:-1]) + '/'
            self.ftp_dst = self.dst.split('flash:/')[1].rstrip()
        if self._remote_dir[-2:] == ':/':
            self.remote_dir_exists = True
        else:
            self.remote_dir_exists = self._remote_dir_exists()

        self.port = port

    def _get_flash_size(self):
        """Return the available space in the remote directory.
        """
        rsp = self.device.cli_display('dir ' + self._remote_dir)
        match = re.search(r'\((\d+)(\s+KB\s+free\))', rsp)

        try:
            return int(match.group(1)) * 1000
        except (ValueError, Exception):
            return 0

    def _enough_space(self):
        """Check for enough space on the remote device.

        Raises:
            FileNotEnoughSpaceError: if there isn't enough space
                on the remote device.
        """
        flash_size = self._get_flash_size()
        file_size = os.path.getsize(self.src)
        if file_size > flash_size:
            raise FileNotEnoughSpaceError(self.src, file_size, flash_size)

    @property
    def file_already_exists(self):
        """Check to see if there is a remote file with the same
        name and md5 sum.

        Returns:
            ``True`` if exists, ``False`` otherwise.
        """
        if not self.remote_dir_exists:
            return False
        dst_hash = None
        try:
            dst_hash = self._get_remote_md5()
        except (ValueError, Exception):
            pass

        if dst_hash is not None:
            src_hash = self._get_local_md5()
            if src_hash == dst_hash:
                return True

        return False

    def _safety_checks(self):
        """Check to make sure the source file exists,
        and that there's enough space on the device.

        Throws:
            FileNotReadableError: if the local file doesn't
                exist or isn't readable.
        """
        f = None
        try:
            f = open(self.src, "rb")
        except IOError:
            raise FileNotReadableError(self.src)
        finally:
            if f:
                f.close()

        if not self.remote_dir_exists:
            raise FileRemoteDirDoesNotExist(self._remote_dir)

        if self.remote_dir_exists:
            if not self.file_already_exists:
                self._enough_space()

    def _get_remote_md5(self):
        """Return the md5 sum of the remote file,
        if it exists.
        """
        E = action_element_maker()
        top = E.top(
            E.FileSystem(
                E.Files(
                    E.File(
                        E.SrcName(self.dst),
                        E.Operations(
                            E.md5sum()
                        )
                    )
                )
            )
        )

        nc_get_reply = self.device.action(top)
        md5sum = find_in_action('md5sum', nc_get_reply)

        if md5sum is not None:
            return md5sum.text.strip()

    def _get_local_md5(self, block_size=2 ** 20):
        """Get the md5 sum of the local file,
        if it exists.
        """
        m = hashlib.md5()
        with open(self.src, "rb") as f:
            buf = f.read(block_size)
            while buf:
                m.update(buf)
                buf = f.read(block_size)
        return m.hexdigest()

    def _remote_dir_exists(self):
        """Check to see if the remote directory exists.
        """
        E = data_element_maker()
        top = E.top(
            E.FileSystem(
                E.Files(
                    E.File(
                        E.Name(self._remote_dir.rstrip('/')),
                        E.IsDirectory()
                    )
                )
            )
        )

        nc_get_reply = self.device.get(('subtree', top))
        is_dir = find_in_data('IsDirectory', nc_get_reply)

        if is_dir is not None \
                and is_dir.text == 'true':
            return True

        return False

    def create_remote_dir(self):
        """Create the remote directory.

        Raises:
            FileCreateDirectoryError: if the directory could
                not be created.
        """
        E = action_element_maker()
        top = E.top(
            E.FileSystem(
                E.Files(
                    E.File(
                        E.SrcName(self._remote_dir.strip('/')),
                        E.Operations(
                            E.MkDir()
                        )
                    )
                )
            )
        )

        self.device.action(top)
        self.remote_dir_exists = True

    def transfer_file(self, hostname, username, password, look_for_keys=False):
        """Transfer the file to the remote device over SCP.

        Note:
            If any arguments are omitted, the corresponding attributes
            of the ``self.device`` will be used.
        Args:
            hostname (str): REQUIRED - The name or
                IP address of the remote device.
            username (str): REQUIRED - The SSH username
                for the remote device.
            password (str): REQUIRED - The SSH password
                for the remote device.
            look_for_keys (bool): OPTIONAL - The SSH look_for_keys
                for the remote device.

        Raises:
            FileTransferError: if an error occurs during the file transfer.
            FileHashMismatchError: if the source and
                destination hashes don't match.
            FileNotReadableError: if the local file doesn't exist or isn't readable.
            FileNotEnoughSpaceError: if there isn't enough space on the device.
            FileRemoteDirDoesNotExist: if the remote directory doesn't exist.
        """
        if not HAS_PARAMIKO:
            raise ImportError('paramiko')
        if not HAS_SCP:
            raise ImportError('scp')
        self._safety_checks()
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            port=self.port,
            allow_agent=False,
            look_for_keys=look_for_keys)

        scp = SCPClient(ssh.get_transport())
        try:
            scp.put(self.src, self.dst)
        except Exception:
            raise FileTransferError

        scp.close()

        src_hash = self._get_local_md5()
        dst_hash = self._get_remote_md5()

        if src_hash != dst_hash:
            raise FileHashMismatchError(self.src, self.dst, src_hash, dst_hash)

    def ftp_file(self, hostname, username, password):
        """Transfer the file to the remote device over FTP.

        Note:
            If any arguments are omitted, the corresponding attributes
            of the ``self.device`` will be used.

        Args:
            hostname (str): OPTIONAL - The name or
                IP address of the remote device.
            username (str): OPTIONAL - The SSH username
                for the remote device.
            password (str): OPTIONAL - The SSH password
                for the remote device.

        Raises:
            FileTransferError: if an error occurs during the file transfer.
            FileHashMismatchError: if the source and
                destination hashes don't match.
            FileNotReadableError: if the local file doesn't exist or isn't readable.
            FileNotEnoughSpaceError: if there isn't enough space on the device.
            FileRemoteDirDoesNotExist: if the remote directory doesn't exist.
        """
        self._safety_checks()
        ftp = FTP()
        ftp.connect(hostname, 21)
        ftp.login(username, password)
        buffer_size = 1024
        fp = open(self.src, 'rb')
        try:
            ftp.storbinary('STOR ' + self.ftp_dst, fp, buffer_size)
        except FileTransferError:
            raise Exception("There was an error while the file was in transit.")
        fp.close()
        ftp.quit()

        src_hash = self._get_local_md5()
        dst_hash = self._get_remote_md5()

        if src_hash != dst_hash:
            raise FileHashMismatchError(self.src, self.dst, src_hash, dst_hash)

    def ftp_downloadfile(self, hostname=None, username=None, password=None):
        """Transfer the file to the remote device over FTP.

        Note:
            If any arguments are omitted, the corresponding attributes
            of the ``self.device`` will be used.

        Args:
            hostname (str): OPTIONAL - The name or
                IP address of the remote device.
            username (str): OPTIONAL - The SSH username
                for the remote device.
            password (str): OPTIONAL - The SSH password
                for the remote device.

        Raises:
            FileTransferError: if an error occurs during the file transfer.
            FileHashMismatchError: if the source and
                destination hashes don't match.
            FileNotReadableError: if the local file doesn't exist or isn't readable.
            FileNotEnoughSpaceError: if there isn't enough space on the device.
            FileRemoteDirDoesNotExist: if the remote directory doesn't exist.
        """
        ftp = FTP()
        ftp.connect(hostname, 21)
        ftp.login(username, password)
        ftp.set_debuglevel(2)
        try:
            ftp.retrbinary('RETR ' + str(self.ftp_dst), open(str(self.src), 'wb').write)
        except FileTransferError:
            raise Exception("There was an error while the file was in transit.")
        ftp.quit()

        src_hash = self._get_local_md5()
        dst_hash = self._get_remote_md5()

        if src_hash != dst_hash:
            raise FileHashMismatchError(self.src, self.dst, src_hash, dst_hash)
