"""Manage FTP on COM7 devices.
author: liudongxue
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    nc_element_maker, config_element_maker)


class Ftp(object):

    def __init__(self, device, state):
        self.device = device
        self.state = state

    def config_ftp(self, stage=False):
        EN = nc_element_maker()
        EC = config_element_maker()
        config = EN.config(
            EC.top(
                EC.FTP(
                    EC.Server(
                        EC.State(self.state)
                    )
                )
            )
        )
        if stage:
            return self.device.stage_config(config, 'edit_config')
        else:
            return self.device.edit_config(config)
