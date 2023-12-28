"""Feature-specific errors.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.errors import PYCW7Error


class FeatureError(PYCW7Error):
    def __init__(self):
        pass


class LengthOfStringError(FeatureError):

    def __init__(self, param_name):
        # passing in the name of the variable rather than the actual string
        # but feel free to pass in the value instead if you want!
        self.param_name = param_name

    def __repr__(self):
        errstr = 'Maximum string length of exceeded for {0}'.format(
            self.param_name)
        return errstr

    __str__ = __repr__


class InvalidIPAddress(FeatureError):

    def __init__(self, ipaddr):
        self.ipaddr = ipaddr

    def __repr__(self):
        errstr = 'Invalid IPv4 or IPv6 Address: {0}'.format(
            self.ipaddr)
        return errstr

    __str__ = __repr__


##################################
#       INTERFACE ERRORS         #
##################################


class InterfaceError(FeatureError):
    def __init__(self, if_name):
        self.if_name = if_name


class InterfaceTypeError(InterfaceError):
    def __init__(self, if_name, if_types=None):
        super(InterfaceTypeError, self).__init__(if_name)
        self.if_types = if_types

    def __repr__(self):
        errstr = '{0} is not a valid interface type.'.format(self.if_name)
        if self.if_types:
            errstr += ' Type must be one of {0}'.format(self.if_types)

        return errstr

    __str__ = __repr__


class InterfaceAbsentError(InterfaceError):
    def __init__(self, if_name):
        super(InterfaceAbsentError, self).__init__(if_name)

    def __repr__(self):
        return 'Interface {0} not found on the device.'.format(self.if_name)

    __str__ = __repr__


class InterfaceParamsError(InterfaceError):
    def __init__(self, if_name, params):
        super(InterfaceParamsError, self).__init__(if_name)
        self.params = params

    def __repr__(self):
        return 'Interface {0} does not take parameters {1}.'.format(
            self.if_name, self.params)

    __str__ = __repr__


class InterfaceMtuParamsError(InterfaceError):
    def __init__(self, if_name, params):
        super(InterfaceMtuParamsError, self).__init__(if_name)
        self.params = params

    def __repr__(self):
        return 'MTU is not in the right range of interface. name: {0}, params: {1}'.format(
            self.if_name, self.params)

    __str__ = __repr__


class InterfaceJumboParamsError(InterfaceError):
    def __init__(self, if_name, params):
        super(InterfaceJumboParamsError, self).__init__(if_name)
        self.params = params

    def __repr__(self):
        return 'MTU is not in the right range of interface. name: {0}, params: {1}'.format(
            self.if_name, self.params)

    __str__ = __repr__


class InterfaceCreateError(InterfaceError):
    def __init__(self, if_name):
        super(InterfaceCreateError, self).__init__(if_name)

    def __repr__(self):
        return 'Interface {0} could not be created.'.format(self.if_name)

    __str__ = __repr__


class InterfaceRemoveError(InterfaceError):
    def __init__(self, if_name):
        super(InterfaceRemoveError, self).__init__(if_name)

    def __repr__(self):
        return 'Interface {0} could not be removed.'.format(self.if_name)

    __str__ = __repr__


class InterfaceVlanMustExist(InterfaceError):
    def __init__(self, if_name, number):
        super(InterfaceVlanMustExist, self).__init__(if_name)
        self.number = number

    def __repr__(self):
        return 'Vlan {0} must exist before interface can be created.'.format(
            self.number)

    __str__ = __repr__


##################################
#       vsi ERRORS               #
##################################

class VsiError(FeatureError):
    def __init__(self):
        pass


class VsiParamsError(VsiError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'There is an error in the provided parameters'

    __str__ = __repr__


class MacaddrFormatError(VsiError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'Wrong parameter format MAC address {0}.'.format(self.params) + \
            ' The correct format is H-H-H'

    __str__ = __repr__


class MacaddrParamsError(VsiError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'Invalid MAC address {0}.'.format(self.params)

    __str__ = __repr__


##################################
#       stp ERRORS               #
##################################

class StpError(FeatureError):
    def __init__(self):
        pass


class StpParamsError(StpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'stp bpdu params must be one of [true,false] '

    __str__ = __repr__


##################################
#       bgp ERRORS               #
##################################

class BgpError(FeatureError):
    def __init__(self):
        pass


class BgpRelyParamsError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'there is error of the params {0}'.format(self.params)

    __str__ = __repr__


class BgpParamsError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'The provided bgp {0} is not in the correct range'.format(self.params)

    __str__ = __repr__


class InstanceParamsError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'The provided instance {0} is out of range'.format(self.params)

    __str__ = __repr__


class GroupParamsError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'The provided group {0} is out of range'.format(self.params)

    __str__ = __repr__


class PeerParamsError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'The provided peer {0} is out of range'.format(self.params)

    __str__ = __repr__


class BgpMissParamsError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'Missing required parameter {0}'.format(self.params)

    __str__ = __repr__


class BgpAfParamsError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'The provided params {0} got an incorrect parameter range'.format(self.params) + \
            ', please carefully check it.'

    __str__ = __repr__


class BgpAfConfigError(BgpError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'Address family vpnv4 or vpnv6 has no value {0} '.format(self.params)

    __str__ = __repr__


##################################
#       local user ERRORS               #
##################################

class LocaluserError(FeatureError):
    def __init__(self):
        pass


class GroupNameError(LocaluserError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'local user group name must be within 1~32 string '

    __str__ = __repr__


class LocaluserLevelError(LocaluserError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'user role level must be in level 0~15 '

    __str__ = __repr__


class LocaluserPasswordError(LocaluserError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'user role password must be in 1~63 length '

    __str__ = __repr__


class LocaluserNameError(LocaluserError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'local user name must be in 1~55 length '

    __str__ = __repr__


class HwtacacsParamsError(LocaluserError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'hwtacacs auth/author/accounting host name can not be config with \
                auth/author/accounting host ip at the same time '

    __str__ = __repr__


######################
# AAA ERRORS #
class AaaError(FeatureError):
    def __init__(self):
        pass


class AaaConfigAbsentError(AaaError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'scheme_name_list must be config while scheme_list exist '

    __str__ = __repr__


class AaaSuperError(AaaError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'if acccess type is super there is only hwtacacs and radius method type '

    __str__ = __repr__


######################
# ospf ERRORS #
class OspfError(FeatureError):
    def __init__(self):
        pass


class OspfParamsError(OspfError):
    def __init__(self, params):
        self.params = params

    def __repr__(self):
        return 'there is error in getting ospf paramater {0}'.format(self.params)

    __str__ = __repr__


######################
# IPINTERFACE ERRORS #
######################

class IpInterfaceError(FeatureError):
    pass


class IpIfaceMissingData(IpInterfaceError):
    def __init__(self):
        super(IpIfaceMissingData, self).__init__()

    def __repr__(self):
        return 'IP address and mask must be supplied'

    __str__ = __repr__


##################################
#       VLAN ERRORS             #
##################################


class VlanError(FeatureError):
    pass


class PriorityError(FeatureError):
    pass


class LldpError(FeatureError):
    pass


class VlanIDError(VlanError):

    def __repr__(self):
        errstr = 'VLAN ID must be between 1-4094'

        return errstr

    __str__ = __repr__


##################################
#       REBOOT ERRORS            #
##################################
class PriorityIdError(PriorityError):

    def __repr__(self):
        errstr = 'priority Id must be between 0-65535'

        return errstr

    __str__ = __repr__


##################################
#       REBOOT ERRORS            #
##################################

##################################
#       REBOOT ERRORS            #
##################################
class LLDPError(LldpError):

    def __repr__(self):
        errstr = 'the value you provide does not between permitted range,please check it again'

        return errstr

    __str__ = __repr__


##################################
#       REBOOT ERRORS            #
##################################

class RebootError(FeatureError):
    pass


class RebootTimeError(RebootError):

    def __repr__(self):
        errstr = 'Format for time must be HH:MM'
        return errstr

    __str__ = __repr__


class RebootDateError(RebootError):

    def __repr__(self):
        errstr = 'Format for the date must be MM/DD/YYYY'
        return errstr

    __str__ = __repr__


##################################
#       PORTCHANNEL ERRORS       #
##################################


class PortChannelError(FeatureError):
    def __init__(self):
        pass


class InvalidPortType(PortChannelError):
    def __init__(self, if_name, config_type, pc_type):
        self.if_name = if_name
        self.config_type = config_type
        self.pc_type = pc_type

    def __repr__(self):
        errstr = ('Proposed port-channel type of "{0}" '.format(self.pc_type)
                  + '\ndoes not match existing physical interface '
                  + '\nof port type "{0}" '.format(self.config_type)
                  + 'on interface: "{0}"'.format(self.if_name))
        return errstr

    __str__ = __repr__


class AggregationGroupError(PortChannelError):
    def __init__(self, if_name):
        self.if_name = if_name

    def __repr__(self):
        errstr = ('interface {0}'.format(self.if_name)
                  + ' is assigned \nto another aggregation group.'
                  + 'It needs to be \nremoved first.')

        return errstr

    __str__ = __repr__


##################################
#       FILE COPY ERRORS         #
##################################


class FileError(FeatureError):
    def __init__(self, src=None, dst=None):
        self.src = src
        self.dst = dst


class FileNotReadableError(FileError):
    def __repr__(self):
        return '{0} doesn\'t exist, or isn\'t readable.'.format(self.src)

    __str__ = __repr__


class FileNotEnoughSpaceError(FileError):
    def __init__(self, src, file_size, flash_size):
        super(FileNotEnoughSpaceError, self).__init__(src)
        self.file_size = file_size
        self.flash_size = flash_size

    def __repr__(self):
        return 'Not enough space on remote device for {0}.\n'.format(self.src) + \
            'File Size: {0} bytes\n'.format(self.file_size) + \
            'Space Available: {0} bytes\n'.format(self.flash_size)

    __str__ = __repr__


class FileTransferError(FileError):
    def __repr__(self):
        return 'There was an error while the file was in transit.'

    __str__ = __repr__


class FileHashMismatchError(FileError):
    def __init__(self, src, dst, src_hash, dst_hash):
        super(FileHashMismatchError, self).__init__(src, dst)
        self.src_hash = src_hash
        self.dst_hash = dst_hash

    def __repr__(self):
        return 'The MD5 hash digests do not match.\n' + \
            'The hash of the source {0} was {1}.\n'.format(self.src, self.src_hash) + \
            'The hash of the destinatino {0} was {1}.\n'.format(self.dst, self.dst_hash)

    __str__ = __repr__


class FileRemoteDirDoesNotExist(FileError):
    def __init__(self, remote_dir):
        self.remote_dir = remote_dir

    def __repr__(self):
        return 'The remote directory {0}'.format(self.remote_dir) + \
            ' does not exist.'

    __str__ = __repr__


##################################
#       Config Errors            #
##################################

class ConfigError(FeatureError):
    pass


class InvalidConfigFile(ConfigError):

    def __repr__(self):
        errstr = ('Config replace operation failed.\n' +
                  ' Validate the config file being applied.')

        return errstr

    __str__ = __repr__


##################################
#       IRF Errors              #
##################################


class IRFError(FeatureError):
    pass


class IRFMemberDoesntExistError(IRFError):

    def __init__(self, member_id):
        self.member_id = member_id

    def __repr__(self):
        return 'The IRF member {0}'.format(self.member_id) + \
            ' does not exist.'

    __str__ = __repr__
