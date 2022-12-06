#!/usr/bin/env python3

from netmiko import ConnectHandler
import meraki
import re
import json

def main():
    cisco1 = {
        "device_type": "cisco_ios",
        "host": "1.1.1.1",
        "username": "test",
        "password": "test",
    }
    API_KEY = '0987654321poiuytrewqlkjhgfdsamnbvcxz'
    dashboard = meraki.DashboardAPI(API_KEY)
    config = []
    mac = []
    serialId = ['1111-1111-1111','2222-2222-2222']

    # CMD EXECUTED
    cli = ['show running-config', 'show interfaces status', 'show mac address-table']
    # Log files
    logs = ['config.log', 'status.log', 'table.log']

    #READING CONFIG FILES
    with ConnectHandler(**cisco1) as net_connect:
        i = 0
        for command in cli:
            output = net_connect.send_command(command)
            with open(logs[i],'w+') as f:
                f.write(output)
            i += 1

    #CONVERTING OLD DATA CONFIG TO JSON
    with open('table.log','r') as f:
        lines = f.readlines()
    for line in lines:
        obj = re.search(r'\s+(\d+)\s+([0-9a-f.]+)\s+DYNAMIC\s+(Gi\d+/\d+/\d+)', line)
        if obj is not None:
            mac.append({'vlan':obj.group(1), 'mac':obj.group(2), 'if':obj.group(3)})
    with open('mac.json', 'w') as f:
        json.dump(mac, f)
#-----------------------------------------------------------------------------------------------------------CODE TO FILTER LOCAL MAC ADDR FROM MAC ADDR LEARNED FROM TRUNK
# with open('response.json', 'r') as f:
#     data = json.load(f)
# empty = []
# for chunk in data:
#     if chunk['switchport'] != '49' and chunk['switchport'] != '48':
#         empty.append(chunk)
#
# with open('test.json', 'w') as f:
#     json.dump(empty, f)
#-----------------------------------------------------------------------------------------------------------
    index = 0
    partial_config = {}
    with open('config.log','r') as f:
        lines = f.readlines()
    for line in lines:
        if index == 0:
            obj = re.search(r'interface GigabitEthernet(\d+/\d+/\d+)', line)
            if obj is not None:
                partial_config['port_id'] = 'Gi' + obj.group(1)
                index += 1
                continue
        if index == 1:
            obj = re.search(r'!', line)
            if obj is not None:
                config.append(partial_config)
                index = 0
                partial_config = {}
            else:
                obj = re.search(r'switchport access vlan (\d+)', line)
                if obj is not None:
                    partial_config['vlan'] = obj.group(1)
                else:
                    obj = re.search(r'switchport voice vlan (\d+)', line)
                    if obj is not None:
                        partial_config['voiceVlan'] = obj.group(1)
                    else:
                        obj = re.search(r'description ([a-zA-Z0-9\- ]+)', line)
                        if obj is not None:
                            partial_config['name'] = obj.group(1)

    with open('config.json', 'w') as f:
        json.dump(config, f)

    with open('config.json', 'r') as f:
        data = json.load(f)

    for i in data:
        obj = re.search(r'Gi(\d+)\/0\/(\d+)', i['port_id'])
        serial = serialId[int(obj.group(1)) - 1]
        port_id = obj.group(2)
        name = ''
        if 'name' in i.keys():
            name = i['name']
        vlan = 1
        typee = 'trunk'
        poeEnabled = False
        if 'vlan' in i.keys():
            vlan = int(i['vlan'])
            typee = 'access'
            poeEnabled = True
        voiceVlan = 1
        if 'voiceVlan' in i.keys():
            voiceVlan = int(i['voiceVlan'])

        response = dashboard.switch.updateDeviceSwitchPort(
            serial, port_id,
            name=name,
            enabled=True,
            type=typee,
            vlan=vlan,
            voiceVlan=voiceVlan,
            poeEnabled=poeEnabled,
            linkNegotiation='Auto negotiate',
        )

if __name__ == '__main__':
	main()
