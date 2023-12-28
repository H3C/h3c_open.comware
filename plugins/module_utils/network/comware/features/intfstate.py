"""Operation for Configuration comparison in COM7 devices.
"""
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class IntfState(object):
    """This class is used to get data and configure a specific File.

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    Attributes:
        device (COM7): connected instance of a ``comware.comware.COM7``
            object.

    """

    def __init__(self, device):
        self.device = device

    def get_result(self):
        # 获取设备接口列表
        commands = 'dis interface brief'
        res = self.device.cli_display(commands)

        res = res.replace('Brief information on interfaces in bridge mode:', '')
        res = res.replace('Link: ADM - administratively down; Stby - standby', '')
        res = res.replace('Speed: (a) - auto', '')
        res = res.replace('Duplex: (a)/A - auto; H - half; F - full', '')
        res = res.replace('Type: A - access; T - trunk; H - hybrid', '')
        res = res.replace('Interface            Link Speed     Duplex Type PVID Description', '')

        ele = res.split('\n')
        element = ele[6:-1]
        length = len(element)
        i = 0
        intfList = []
        # 获取接口列表
        while i < length - 1:
            intf = element[i].split(' ')[0]
            intfList.append(intf)
            i += 1
            if i > length:
                break
        list_1 = [i for i in intfList if i != '\r']
        list_2 = [i for i in list_1 if i != '']  # 接口列表，长度60

        # 获取设备接口列表状态
        upList = []
        j = 0
        while j < length:
            up = element[j].split(' ')  # 将字符串按照空格切分
            upList.append(up)

            j += 1
            if j > length:
                break

        upLen = len(upList)  # Up列表长度

        m = 0
        UPlist = []
        while m < upLen - 1:

            a = [p for p in upList[m] if p != '\r']
            b = [p for p in a if p != '']
            UPlist.append(b)
            m += 1
            if m > upLen:
                break

        LIST = [x for x in UPlist if x != []]

        lit = []
        e = 0
        while e < len(LIST):
            lit.append(LIST[e][1])
            e += 1
            if e > len(LIST):
                break
        # print (lit)#接口状态列表

        # 打印出接口没有shutdown实际却down的索引号
        down = 'DOWN'
        a = []
        for i, v in enumerate(lit):
            if v == down:
                a.append(list_2[i])

        if len(a):
            return a
        else:
            return False
