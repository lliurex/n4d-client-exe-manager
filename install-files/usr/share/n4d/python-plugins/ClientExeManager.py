import os
import os.path
import hashlib
import random
import netifaces

import pyinotify
from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent

import glob
import threading
import n4d.responses

class ClientExeManager:
	
	ONESHOT_SCRIPTS_PATH="/usr/share/n4d-client-exe-manager/one-shots/"
	BOOT_SCRIPTS="/usr/share/n4d-client-exe-manager/boot-scripts/"
	
	def __init__(self):
		
		self.db={}
		
	#def init

	
	def startup(self,options):
		
		self.generate_database()
		self.start_inotify()
		
	#def startup

	
	def get_mac_from_ip(self,ip):
	
	
		for item in netifaces.interfaces():
			info=netifaces.ifaddresses(item)
			try:
				if info[netifaces.AF_INET][0]["addr"]==ip:
					return info[netifaces.AF_LINK][0]["addr"]
			except Exception as e:
				print(str(e))
				
		return None
	
		
	#def get_mac_from_ip

	
	def md5sum(self,path):
		
		try:
		
			with open(path, 'rb') as fh:
				m = hashlib.md5()
				while True:
					data = fh.read(8192)
					if not data:
						break
					m.update(data)
				return m.hexdigest()
		except Exception as e:
			print(str(e))
			return "MD5SUM-ERROR-"+str(random.random())
		
	#def md5sum

	
	def generate_database(self,path=None):
		
		self.db={}
		
		if path==None:
			path=ClientExeManager.ONESHOT_SCRIPTS_PATH
		
		for item in sorted(os.listdir(path)):
			file_path=path+item
			md5=self.md5sum(file_path)
			self.db[md5]=file_path
			
	#def generate_database


	def start_inotify(self):

		t=threading.Thread(target=self._inotify)
		t.daemon=True
		t.start()

	#def start_inotify


	def _inotify(self,folder=None):
		
		if folder==None:
			folder=ClientExeManager.ONESHOT_SCRIPTS_PATH
		
		wm=WatchManager()
		mask=pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_MODIFY
		
		class Process_handler(ProcessEvent):
			
			def __init__(self,main):
				self.main=main
			
			def process_IN_CREATE(self,event):
				
				self.main.generate_database()
				
			def process_IN_DELETE(self,event):	
				
				self.main.generate_database()
				
			def process_IN_MODIFY(self,event):
				
				self.main.generate_database()
	
		notifier=Notifier(wm,Process_handler(self))
		
		wdd=wm.add_watch(folder,mask,rec=True)
		
		while True:
			try:
				
				notifier.process_events()
				if notifier.check_events():
					notifier.read_events()
				
			except Exception as e:
				notifier.stop()
				print(str(e))
				
	
	#def _inotify


	def get_available_oneshots(self,filter_list=[]):
		
		ret=[]
		
		if type(filter_list)!=type([]):
			filter_list=[]
		
		
		
		for item in self.db:
			if item not in filter_list:
				f=open(self.db[item],"rb")
				content="".join(f.readlines())
				f.close()
				ret.append((item,content))
				
		#Old n4d:return ret
		return n4d.responses.build_successful_call_response(ret)
	
	#def get_available_oneshots
	
	
	def get_boot_scripts(self,mac=None):
		
		ret=[]
		
		for item in glob.glob(ClientExeManager.BOOT_SCRIPTS+"/common/*"):
			if os.path.isfile(item):
				f=open(item)
				ret.append(f.readlines())
				f.close()
		
		if mac!=None:
			
			mac=mac.replace(":","").lower()
			print(mac)
			if os.path.exists(ClientExeManager.BOOT_SCRIPTS+mac):
				for item in glob.glob(ClientExeManager.BOOT_SCRIPTS+mac+"/*"):
					if os.path.isfile(item):
						f=open(item)
						ret.append(f.readlines())
						f.close()
		
		#Old n4d:return {"status":True,"data":ret}
		return n4d.responses.build_successful_call_response(ret)
		
		
	#def get_boot_scripts
	
	
#class ClientExeManager

if __name__=="__main__":
	
	cem=ClientExeManager()
	cem.startup(None)
	print(cem.get_available_oneshots(["159d56c4e63112c39b3309e709a4d0ee"]).get('return',None))