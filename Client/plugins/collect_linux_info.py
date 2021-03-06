#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import subprocess

def collect():
	filter_key = ["Manufacturer","Serial Number","Product Name","UUID","Wake-up Type"]
	raw_data = {}

	for key in filter_key:
		try:
			res = subprocess.Popen("sudo dmidecode -t system|grep '{}'".format(key),stdout=subprocess.PIPE,shell=True)
			result = res.stdout.read().decode()
			data_list = result.split(":")

			if len(data_list) > 1:
				raw_data[key] = data_list[1].strip()
			else:
				raw_data[key] = ''
		except Exception as e:
			print(e)
			raw_data[key] = ''

	data = dict()
	data['asset_type'] = 'server'
	data['manufacturer'] = raw_data['Manufacturer']
	data['sn'] = raw_data['Serial Number']
	data['uuid'] = raw_data['UUID']
	data['wake_up_type'] = raw_data['Wake-up Type']

	data.update(get_os_info())
	data.update(get_cpu_info())
	data.update(get_ram_info())
	data.update(get_nic_info())
	# data.update(get_disk_info())

	return data

def subprocess_popen(command):
	info = subprocess.Popen(command,stdout=subprocess.PIPE,shell=True)
	info = info.stdout.read().decode()
	return info

def get_os_info():
	"""
	获取操作系统信息
	:return:
	"""
	distributor = subprocess_popen("lsb_release -a|grep 'Distributor ID'").split(":")
	release = subprocess_popen("lsb_release -a|grep 'Description'").split(":")
	data_dic = {
		"os_distribution": distributor[1].strip() if len(distributor) > 1 else "",
		"os_release": release[1].strip() if len(release) > 1 else "",
		"os_type": "Linux",
	}
	return data_dic

def get_cpu_info():
	"""
	获取cpu信息
	:return:
	"""
	data = dict()
	data["cpu_count"] = subprocess_popen("cat /proc/cpuinfo| grep 'physical id'| sort| uniq| wc -l").strip()
	data["cpu_core_count"] = subprocess_popen("cat /proc/cpuinfo| grep 'cpu cores'| uniq").strip()
	cpu_model = subprocess_popen("cat /proc/cpuinfo |grep 'model name' |head -1").strip().split(":")

	if len(cpu_model) > 1:
		data["cpu_model"] = cpu_model[1].strip()
	else:
		data["cpu_model"] = ''

	return data

def get_ram_info():
	"""
	获取内存信息
	:return:
	"""
	raw_list = subprocess_popen("sudo dmidecode -t memory").split("\n")
	raw_ram_list = []
	item_list = []
	for line in raw_list:
		if line.startswith("Memory Device"):
			raw_ram_list.append(item_list)
			item_list = []
		else:
			item_list.append(line.strip())

	ram_list = []
	for item in raw_ram_list:
		item_ram_size = 0
		ram_item_to_dic = {}
		for i in item:
			data = i.split(":")
			if len(data) == 2:
				key, v = data
				if key == "Size":
					if v.strip() != "No Module Installed":
						ram_item_to_dic['capacity'] = v.split()[0].strip()
						item_ram_size = round(float(v.split()[0]))
					else:
						ram_item_to_dic['capacity'] = 0

				if key == 'Type':
					ram_item_to_dic['model'] = v.strip()
				if key == 'Manufacturer':
					ram_item_to_dic['manufacturer'] = v.strip()
				if key == 'Serial Number':
					ram_item_to_dic['sn'] = v.strip()
				if key == 'Asset Tag':
					ram_item_to_dic['asset_tag'] = v.strip()
				if key == 'Locator':
					ram_item_to_dic['slot'] = v.strip()

		if item_ram_size == 0:
			pass
		else:
			ram_list.append(ram_item_to_dic)

	raw_total_size = subprocess_popen("cat /proc/meminfo|grep Memtotal").split(":")
	ram_data = {'ram':ram_list}
	if len(raw_total_size) == 2:
		total_gb_size = int(raw_total_size[1].split()[0])/(1024**2)
		ram_data['ram_size'] = total_gb_size

	return ram_data

def get_nic_info():
	"""
	获取网卡信息
	:return:
	"""
	raw_data = subprocess_popen("ifconfig -a").split("\n")

	nic_dic = dict()
	next_ip_line = False
	last_mac_addr = None

	for line in raw_data:
		if next_ip_line:
			next_ip_line = False
			nic_name = last_mac_addr.split()[0]
			mac_addr = last_mac_addr.split("HWaddr")[1].strip()
			raw_ip_addr = line.split("inet addr:")
			raw_bcast = line.split("Bcast:")
			raw_netmask = line.split("Mask:")
			if len(raw_ip_addr) > 1:
				ip_addr = raw_ip_addr[1].split()[0]
				network = raw_bcast[1].split()[0]
				netmask = raw_netmask[1].split()[0]
			else:
				ip_addr = None
				network = None
				netmask = None
			if mac_addr not	in nic_dic:
				nic_dic[mac_addr] = {'name':nic_name,
									 'mac': mac_addr,
									 'net_mask': netmask,
									 'network': network,
									 'bonding': 0,
									 'model': 'unknown',
									 'ip_address': ip_addr,
									 }
			else:
				if '{}_boding_addr'.format((mac_addr,)) not in nic_dic:
					random_mac_addr = '{}_bonding_addr'.format((mac_addr,))
				else:
					random_mac_addr = '{}_bonding_addr2'.format((mac_addr,))
				nic_dic[random_mac_addr] = {'name': nic_name,
                                            'mac': random_mac_addr,
                                            'net_mask': netmask,
                                            'network': network,
                                            'bonding': 1,
                                            'model': 'unknown',
                                            'ip_address': ip_addr,
											}

		if "HWaddr" in line:
			next_ip_line = True
			last_mac_addr = line

	nic_list = []
	for k,v in nic_dic.items():
		nic_list.append(v)

	return {'nic':nic_list}

def get_disk_info():
	"""
	获取存储信息。
	本脚本只针对ubantu中使用sda，且只有一块硬盘的情况
	:return:
	"""
	# raw_data = subprocess.Popen("sudo hdparm -i /dev/sda | grep Model", stdout=subprocess.PIPE, shell=True)
	# raw_data = raw_data.stdout.read().decode()
	# data_list = raw_data.split(",")
	# model = data_list[0].split(":")[1]
	# sn = data_list[2].split(":")[1].strip()
	#
	# size_data = subprocess.Popen("sudo fdisk -l /dev/sda | grep Disk|head -1", stdout=subprocess.PIPE, shell=True)
	# size_data = size_data.stdout.read().decode()
	# size = size_data.split(":")[1].strip().split(" ")[0]
	#
	result = {'physical_disk_driver': []}
	disk_dict = dict()
	disk_dict["model"] = subprocess_popen("dmidecode -s system-product-name")
	disk_dict["size"] = size
	disk_dict["sn"] = subprocess_popen("dmidecode -s system-serial-number")
	result['physical_disk_driver'].append(disk_dict)

	return result

if __name__ == '__main__':
    # 收集信息功能测试
	data = collect()
	print(data)
