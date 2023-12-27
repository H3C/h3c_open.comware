from ansible_collections.h3c_open.comware.plugins.module_utils.network.comware.utils.xml.lib import *
class MacUnicastTable(object):

    """This class is used to get MacUnicastTable

    Args:
        device (COM7): connected instance of a ``comware.comware.COM7``  object.

    """

    def __init__(self, device):
        self.device = device

    def getMacTableTop(self):        
        """Build XML object for MacTable

        Returns:
            XML object for MacTable data
        """        
        E = data_element_maker()
        top = E.top(
            E.MAC(
                E.MacUnicastTable(
                    E.Unicast()
                )
            )
        )
        return top

    def getMacList(self):        
        """get macList 
        
        Returns:
            macList(list)
        """
        macList = []
        macMap = {}
        macTableTop = self.getMacTableTop()
        ruleTop = self.device.get(('subtree', macTableTop))
        vlanIDList = findall_in_data('VLANID', ruleTop.data_ele)
        macAddList = findall_in_data('MacAddress', ruleTop.data_ele)
        portIndexList = findall_in_data('PortIndex', ruleTop.data_ele)
        statusList = findall_in_data('Status', ruleTop.data_ele)
        agingList = findall_in_data('Aging', ruleTop.data_ele)
        
        for vlanID,macAdd,portIndex,status,aging in zip(vlanIDList,macAddList,portIndexList,statusList,agingList):
            macMap['vlanID'] = vlanID.text
            macMap['macAdd'] = macAdd.text
            macMap['portIndex'] = portIndex.text
            macMap['status'] = status.text
            macMap['aging'] = aging.text 
            macList.append(macMap.copy())
            macMap.clear()    
        
        for macTable in macList: 
            ifIndexMap = self.getIfIndexMap(macTable.get('portIndex'))  
            macTable['name'] = ifIndexMap.get('Name')
            if macTable['status'] == '0':
                macTable['status'] = 'Other'
            elif macTable['status'] == '1':
                macTable['status'] = 'Security'
            elif macTable['status'] == '2':
                macTable['status'] = 'Learned'
            elif macTable['status'] == '3':
                macTable['status'] = 'Static'
            elif macTable['status'] == '4':
                macTable['status'] = 'Blackhole'  
            del macTable['portIndex']
        
        
        return macList

    def getIfIndexTop(self,ifIndex):        
        """Build XML object for IfIndex data

        Returns:
            XML object for IfIndex data
        """        
        E = data_element_maker()
        top = E.top(
            E.Ifmgr(
                E.Interfaces(
                    E.Interface(
                        E.IfIndex(ifIndex)
                    )
                )
            )
        )
        return top 
    
    def getIfIndexMap(self,ifIndex):        
        """get ifIndexMap 
        
        Returns:
            ifIndexMap(map)
        """
        allIfIndexList = []
        ifIndexMap = {}
        ifIndexTop = self.getIfIndexTop(ifIndex)
        ruleTop = self.device.get(('subtree', ifIndexTop))
        ifIndexList = findall_in_data('IfIndex', ruleTop.data_ele)
        nameList = findall_in_data('Name', ruleTop.data_ele) 
        
        ifIndexMap['IfIndex'] = ifIndexList[0].text
        ifIndexMap['Name'] = nameList[0].text  
        return ifIndexMap
    
    
    
    
    
    
    
    
    
    
    