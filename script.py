from toolkit import *
import time
a = AzureManage()
a.get_hosted_service()
a.get_hosted_storage()
a.get_container()
a.copy_image()
a.register_image()
#a.copy_disk()
a.build_VM('Master-Master')
