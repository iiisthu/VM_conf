from toolkit import *
from cmd_toolkit import *
import time
a = AzureManage()
a.get_hosted_service()
a.get_hosted_storage()
a.get_container()
a.copy_image()
a.register_image()
a.build_VM('master-slave')
a.copy_disk()
a.attach_disk()


b = CMD(a.serv_name + ".chinacloudapp.cn")
b.connect_to_VM()
