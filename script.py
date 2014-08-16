from toolkit import *
import time
a = AzureManage()
a.get_hosted_service()
a.get_hosted_storage()
a.get_container()
a.copy_image()
a.register_image()
a.build_VM('Master-Master')
a.copy_disk()
a.attach_disk()
