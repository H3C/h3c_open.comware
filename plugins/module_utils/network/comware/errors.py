"""Errors for comware library.

(c) Copyright 2016 Hewlett Packard Enterprise Development LP Licensed under the Apache License, Version 2.0
(the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License
at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied. See the License for the specific language governing permissions and limitations under the License.

"""
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    remove_namespaces, get_text
)


class PYCW7Error(Exception):
    """General base class for all errors in the comware library.
    """
    pass


class FeatureError(PYCW7Error):
    """Base class for all errors related to features.
    """
    pass


##################################
#       NETCONF RPC ERRORS       #
##################################


class NCError(PYCW7Error):
    """Wrapper for ncclient RPC errors.
    """

    def __init__(self, rpc_error=None):
        super(NCError, self).__init__()
        self.tag = ''
        if rpc_error:
            self.rpc_error = rpc_error
            self.xml = remove_namespaces(rpc_error.xml)
            self.msg = rpc_error.message
            self.tag = rpc_error.tag
            self.bad_element = get_text(self.xml, 'error-info/bad-element') or ''

    def __repr__(self):
        rep = '{0}: NETCONF Protocol error ({1}).'.format(self.__class__.__name__, self.msg)

        if hasattr(self, 'rpc_error'):
            rep += ' Tag: {0}'.format(self.tag)
            if self.bad_element:
                rep += ' Bad Element: {0}'.format(self.bad_element)

        if self.tag == 'access-denied':
            rep += ' It is possible the device is' \
                   + ' locked by another NETCONF connection.'

        if self.tag == 'invalid-value':
            rep += ' Message: {0}'.format(self.msg)

        return rep

    __str__ = __repr__


class LockConflictError(PYCW7Error):
    """When there's an attempt to lock, and NETCONF lock is not available.
    """

    def __repr__(self):
        return '{0}: Couldn\'t obtain NETCONF lock.'.format(
            self.__class__.__name__) + \
            ' Another connection holds the lock.'

    __str__ = __repr__


class UnlockConflictError(PYCW7Error):
    """When there's an attempt to unlock, and NETCONF lock is not available.
    """

    def __repr__(self):
        return '{0}: Couldn\'t unlock NETCONF lock.'.format(
            self.__class__.__name__) + \
            ' Another connection holds the lock.'

    __str__ = __repr__


##################################
#       TIMEOUT ERRORS         #
##################################


class NCTimeoutError(PYCW7Error):
    """When there is no response from the device within the timeout range.
    """

    def __repr__(self):
        return '{0}: The NETCONF RPC timed out.'.format(
            self.__class__.__name__)

    __str__ = __repr__


##################################
#       CONNECTION ERRORS        #
##################################


class ConnectionError(PYCW7Error):
    """When there is an error in the SSH/NETCONF connection.
    """

    def __init__(self, dev, msg=None):
        super(ConnectionError, self).__init__()
        self.dev = dev
        self.msg = msg
        self.host = dev.host
        self.port = dev.port

    def __repr__(self):
        rep = '{0}: host: {1}, port: {2}'.format(
            self.__class__.__name__, self.host, self.port)
        if self.msg:
            rep += ' msg: {0}'.format(self.msg)

        return rep

    __str__ = __repr__


class ConnectionAuthenticationError(ConnectionError):
    """When there's an authentication error.
    """
    pass


class ConnectionSSHError(ConnectionError):
    """When there's an SSH error.
    """
    pass


class ConnectionUnkownHostError(ConnectionError):
    """When there's an uknown host error.
    """
    pass


class ConnectionClosedError(ConnectionError):
    """When there's a connection closed error.
    """
    pass
