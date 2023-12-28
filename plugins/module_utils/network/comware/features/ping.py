"""Ping another device from COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.features.errors import InvalidIPAddress
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.validate import valid_ip_network
from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import (
    action_element_maker, find_in_action, findall_in_action)


class Ping(object):
    """Ping another device from an COM7 device.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        host (str): IP address or name to ping from the switch
        vrf (vrf): source VRF on the switch the ping will come from
        v6 (bool): set to true if dest is v6 target
        detail (bool): set to true if you want to see per ping
            (ICMP echo request) response details

    Note:
        If an IPv6 address is provided for ``host``, there is no need
        to set ``v6`` to ``True``, but it doesn't hurt either way.

        If a name is used for ``host`` and that resolves to a v6 address,
        then ``v6`` must be set to ``True``.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.
        host (str): IP address or name to ping from the switch
        vrf (vrf): source VRF on the switch the ping will come from
        v6 (bool): set to true if dest is v6 target
        detail (bool): set to true if you want to see per ping
            (ICMP echo request) response details
        response (dict): see ``_ping``

    """

    def __init__(self, device, host, vrf='', v6=False, detail=False):
        self.device = device
        self.host = host
        self.vrf = vrf or ''
        self.v6 = v6
        self.detail = detail

        # list of XML tags used to build proper objects
        self.v4tags = ['Ping', 'IPv4Ping', 'PingTest']
        self.v6tags = ['Ping', 'IPv6Ping', 'PingTest']

        self.response = self._ping()

    def _ping(self):
        """Builds XML object for VLAN configuration and sends to staging

        Returns:
            It returns a dictionary with the following k/v pairs:

                :payload_length (str): bytes of payload
                :max (str): represents max response time in milliseconds
                :min (str): represents min response time in milliseconds
                :avg (str): represents avg response time in milliseconds
                :packets_tx (str): number of packets sent
                :packets_rx (str): number of packets received
                :host (str): target host being "pinged"
                :loss_rate (str): percent of which pings are dropped
                :detailed_response (list): list of dicts that provides
                    detail for each icmp request including icmp seq #
                    and reply time.

        """
        if '.' in self.host or ':' in self.host:
            self.param_check(host=self.host)

        E = action_element_maker()
        if ':' in self.host or self.v6 is True:
            top = E.top(
                E.Ping(
                    E.IPv6Ping(
                        E.PingTest(
                            E.Host(self.host),
                            E.VRF(self.vrf)
                        )
                    )
                )
            )
        else:
            top = E.top(
                E.Ping(
                    E.IPv4Ping(
                        E.PingTest(
                            E.Host(self.host),
                            E.VRF(self.vrf)
                        )
                    )
                )
            )

        rsp = self.device.action(top)
        return self._build_response(rsp)

    def _build_response(self, response):
        """Builds dictionary from XML response coming from device
        """
        as_xml = response

        key_map = {
            'payload_length': 'PayloadLength',
            'packets_tx': 'TotalTransmitPacket',
            'packets_rx': 'TotalReceivePacket',
            'loss_rate': 'LossRate',
            'min': 'MinReplyTime',
            'max': 'MaxReplyTime',
            'avg': 'AvgReplyTime',
            'host': 'Host',
            'source': 'SrcAddr'
        }

        def _get_time(time):
            return str(int(find_in_action('ReplyTime', time).text) / 1000)

        ping_response = {}
        for new_key, xml_tag in key_map.items():
            value = ''
            if new_key in ['min', 'avg', 'max']:
                value = _get_time(as_xml)
            else:
                get_obj = find_in_action(xml_tag, as_xml)
                if get_obj is not None:
                    value = get_obj.text
            if value:
                ping_response[new_key] = value
            if self.detail:
                five_replies = findall_in_action('EchoReply', as_xml)
                replies = []
                for reply in five_replies:
                    icmp_seq = find_in_action('IcmpSequence', reply).text
                    reply_time = _get_time(reply)
                    temp = dict(icmp_seq=icmp_seq, reply_time=reply_time)
                    replies.append(temp)
                ping_response['detailed_response'] = replies

        return ping_response

    @staticmethod
    def param_check(**kvargs):
        """Basic param validation for v4 and v6 addresses
        """
        host = kvargs.get('host')
        if host:
            if not valid_ip_network(host):
                raise InvalidIPAddress(host)
