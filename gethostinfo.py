#!/use/bin/env python
#coding:utf-8
# Host Info Collect Agent Process
# Author:tanzhixu

import subprocess

import platform

import urllib

import urllib2

import os

import logging

import logging.handlers

try:
    import json
except ImportError,e:
    import simplejson as json

Collect_data_File = '/tmp/unfae_collect_data.txt'

Log_File = '/tmp/unfae_collect_info.log'

Post_Insert_Url = 'http://10.1.60.57:8000/asset/insert'

Post_Update_Url = 'http://10.1.60.57:8000/asset/update'
		
class GetHostInfo(object):
	"""The class for collect device physical infomation"""
	
	def __init__(self):
		super(GetHostInfo, self).__init__()

	def Popen_For_Readline(self,cmd):
		return subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).stdout.readline().strip('\n').strip()

	def Popen_For_Readlines(self,cmd):
		result = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE).stdout.readlines()
		if len(result) >= 1:
			result_new = []
			for i in range(len(result)):
				result_new.append(result[i].strip('\n'))
		else:
			result_new = result
		return result_new

	def Get_Device_Type(self):
		cmd = "/usr/sbin/dmidecode -t 1|grep Manufacturer|cut -d ':' -f2|cut -d ' ' -f2"
		return self.Popen_For_Readline(cmd)

	def Get_Device_Model(self):
		cmd = "/usr/sbin/dmidecode -t 1|grep 'Product Name'|cut -d : -f2"
		return self.Popen_For_Readline(cmd)

	def Get_Device_Sn(self):
		cmd = "/usr/sbin/dmidecode -t 1|grep 'Serial Number'|cut -d : -f2"
		return self.Popen_For_Readline(cmd)

	def Get_Memory_Slots_Number(self):
		cmd = "/usr/sbin/dmidecode |grep -A16 'Memory Device$'|grep 'Size'|wc -l"
		return self.Popen_For_Readline(cmd)

	def Get_System_Kernel(self):
		cmd = "/bin/uname -a"
		return self.Popen_For_Readline(cmd)

	def Get_Ethernet_Interface(self):
		cmd = "lspci|grep 'Ethernet'"
		return self.Popen_For_Readlines(cmd)

	def Get_Logical_Cpu_Cores(self):
		cmd = "grep -c 'model name' /proc/cpuinfo"
		return self.Popen_For_Readline(cmd)
		
	def Get_Physical_Cpu_Cores(self):
		cmd = "cat /proc/cpuinfo |grep 'physical id'|uniq -c|wc -l"
		return self.Popen_For_Readline(cmd)

	def Get_Physical_Cpu_Model(self):
		cmd = "cat /proc/cpuinfo |grep 'model name' |head -n 1|cut -d : -f2"
		return self.Popen_For_Readline(cmd)

	def Get_System_Version(self):
		return platform.platform()

	def Get_Hard_Disk(self):
		cmd = "parted -l | grep Disk | grep -v mapper |grep -v Flags"
		return self.Popen_For_Readlines(cmd)

	def Get_System_Network_Card(self):
		if 'centos-7' in self.Get_System_Version():
			cmd = "/sbin/ifconfig|grep eno | cut -d: -f1"
		elif 'centos-6' in self.Get_System_Version():
			cmd = "/sbin/ifconfig|grep HWaddr|awk '{print $1}'"
		return self.Popen_For_Readlines(cmd)
	
	def Get_System_Ip(self):
		if 'centos-7' in self.Get_System_Version():
			cmd = "/sbin/ifconfig|grep 'inet '|grep -Ev '127.0.0.1'|awk '{print $2}'"
		elif 'centos-6' in self.Get_System_Version():
			cmd = "/sbin/ifconfig|grep 'inet '|grep -Ev '127.0.0.1'|cut -d: -f2|awk '{print $1}'"
		return self.Popen_For_Readlines(cmd)

	def Get_System_Mac(self):
		if 'centos-7' in self.Get_System_Version():
			def splitData(data):
				ret = []
				d = ''
				for i in  [l for l in data.split('\n') if l]:
					if i[0].strip():
						if d:
							ret.append(d)
						d = i
					else:
						d += '\n' + i
				if d:ret.append(d)
				return ret
			result = subprocess.Popen('/sbin/ifconfig',shell=True,stdout=subprocess.PIPE).stdout.read()
			iflist = splitData(result)
			mac_list = []
			for i in iflist:
				if i.startswith('eno'):
					mac_list.append(i.split('\n')[1].split()[1])
			return mac_list
		elif 'centos-6' in self.Get_System_Version():
			cmd = "/sbin/ifconfig -a|grep 'HWaddr'|grep -v usb0|awk '{print $NF}'"
			return self.Popen_For_Readlines(cmd)

	def Get_System_Hostname(self):
		System_Hostname= platform.node()
		return System_Hostname

	def Get_System_Swap(self):
		cmd = "free -m|grep Swap|awk '{print $2}'"
		return self.Popen_For_Readline(cmd)

	def Get_Physical_Memory(self):
		cmd = """cat /proc/meminfo |grep MemTotal |awk '{print $2/1024, "MB"}'"""
		return self.Popen_For_Readline(cmd)

def Post_Date_Use_Json(url,data):
	data = json.dumps(data) 
	post_data = urllib2.Request(url, data)
	result = urllib2.urlopen(post_data).read()
	return result

def Write_File(data):
	with open(Collect_data_File,'w') as fd:
		fd.write(data)

def Read_File():
	with open(Collect_data_File) as fd:
		return fd.read()

def Json_To_Date(data):
	return json.loads(data)

def Data_To_Json(data):
	return json.dumps(data)

def Logging(log):
	handler = logging.handlers.RotatingFileHandler(Log_File, maxBytes = 1024*1024, backupCount = 5)
	fmt = '%(asctime)s - %(filename)s - %(name)s - %(message)s' 
	formatter = logging.Formatter(fmt)    
	handler.setFormatter(formatter)       
	logger = logging.getLogger('unfae')      
	logger.addHandler(handler)            
	logger.setLevel(logging.DEBUG)  
	logger.info(log)  

def Diff_New_And_Old(Now_Collect_Data,Old_Collect_Data):
	Check_Collect_Data = {}
	for k in Now_Collect_Data:
		if isinstance(Now_Collect_Data[k],str):
			if Now_Collect_Data[k] != Old_Collect_Data[k]:
				Check_Collect_Data[k] = Now_Collect_Data[k]
		elif isinstance(Now_Collect_Data[k],list):
			if len(Now_Collect_Data[k]) == len(Old_Collect_Data[k]):
				for i in range(len(Now_Collect_Data[k])):
					if Now_Collect_Data[k][i] != str(Old_Collect_Data[k][i]):
						Check_Collect_Data[k] = Now_Collect_Data[k]	
			else:
				Check_Collect_Data[k] = Now_Collect_Data[k]
	return Check_Collect_Data

def main():
	Host_Info = GetHostInfo()
	Now_Collect_Data = {
		'Device_Type': Host_Info.Get_Device_Type(), 
		'Device_Model': Host_Info.Get_Device_Model(), 
		'Device_Sn': Host_Info.Get_Device_Sn(), 
		'System_Kernel': Host_Info.Get_System_Kernel(), 
		'Ethernet_Interface': Host_Info.Get_Ethernet_Interface(), 
		'Memory_Slots_Number': Host_Info.Get_Memory_Slots_Number(), 
		'Physical_Memory': Host_Info.Get_Physical_Memory(), 
		'Logical_Cpu_Cores': Host_Info.Get_Logical_Cpu_Cores(), 
		'Physical_Cpu_Cores': Host_Info.Get_Physical_Cpu_Cores(), 
		'Physical_Cpu_Model': Host_Info.Get_Physical_Cpu_Model(), 
		'System_Version': Host_Info.Get_System_Version(), 
		'Hard_Disk': Host_Info.Get_Hard_Disk(), 
		'System_Ip': Host_Info.Get_System_Ip(), 
		'System_Mac': Host_Info.Get_System_Mac(), 
		'System_Hostname': Host_Info.Get_System_Hostname(), 
		'System_Network_Card': Host_Info.Get_System_Network_Card(), 
		'System_Swap': Host_Info.Get_System_Swap()
	}
	if os.path.exists(Collect_data_File):
		Old_Collect_Data = Json_To_Date(Read_File())
		Check_Collect_Data = Diff_New_And_Old(Now_Collect_Data,Old_Collect_Data)
		if Check_Collect_Data:
			Check_Collect_Data['Host_Id'] = Old_Collect_Data['Host_Id']
			Post_Result = Post_Date_Use_Json(Post_Update_Url,Check_Collect_Data)
			Logging(Post_Result)
		Now_Collect_Data['Host_Id'] = Old_Collect_Data['Host_Id']
		Write_File(Data_To_Json(Now_Collect_Data))
	else:
		Post_Result = Post_Date_Use_Json(Post_Insert_Url,Now_Collect_Data)
		Host_Id = Post_Result[1:-1]
		Now_Collect_Data['Host_Id'] = Host_Id
		Write_File(Data_To_Json(Now_Collect_Data))
		Logging(Post_Result)
if __name__ == '__main__':
	main()