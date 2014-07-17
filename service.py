from time import sleep

from azure import *
from azure.servicemanagement import *
from azure.storage import *
from random import Random


class VirtualNetwork:
    vpn_conf_xml = '''<NetworkConfiguration xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.microsoft.com/ServiceHosting/2011/07/NetworkConfiguration">
    <VirtualNetworkConfiguration>
    <Dns />
    <VirtualNetworkSites>
      <VirtualNetworkSite name="{name}" AffinityGroup="{ag_name}">
        <AddressSpace>
          <AddressPrefix>192.168.0.0/20</AddressPrefix>
        </AddressSpace>
        <Subnets>
          <Subnet name="Subnet-1">
            <AddressPrefix>192.168.0.0/23</AddressPrefix>
          </Subnet>
        </Subnets>
      </VirtualNetworkSite>
    </VirtualNetworkSites>
  </VirtualNetworkConfiguration>
</NetworkConfiguration>'''
    
    def __init__(self, sms, name="MyVPN", ag_name="Wonderland"):
        self.sms = sms
        self.name = name
        self.ag_name = ag_name
        self.existed = False
        self.xml = self.vpn_conf_xml.format(name=name, ag_name=ag_name)
    
    def create(self):
        vpn_list = self.sms.list_virtual_network_sites()
        vpn_name_list = [vpn.name for vpn in vpn_list]
        if not self.name in vpn_name_list:
            self.result = self.sms.set_network(self.xml)
        else:
            self.existed = True

    def wait_result(self):
        if self.existed:
            pass
        else:
            vpn_list = self.sms.list_virtual_network_sites()
            vpn_name_list = [vpn.name for vpn in vpn_list]
            while not self.name in vpn_name_list:
                vpn_list = self.sms.list_virtual_network_sites()
                vpn_name_list = [vpn.name for vpn in vpn_list]
                sleep(2)
                print("Virtual network test")
            print("Virtual Network creation finished")
        

class AGroup:
    def __init__(self, sms, name="Wonderland", 
                 label="Wonderland", location="China East"):
        self.name = name
        self.label = label
        self.location = location
        self.sms = sms
        self.result = None
        self.existed = False

    def create(self):
        ag_list = self.sms.list_affinity_groups()
        ag_name_list = [ag.name for ag in ag_list]
        if not self.name in ag_name_list:
            self.result = self.sms.create_affinity_group(self.name, 
                                                         self.label, 
                                                         self.location)
        else:
            self.existed = True
            print("AG exists")
    
    def wait_result(self):
        if self.existed:
            pass
        elif self.result:
            operation_result = self.sms.get_operation_status(self.result.request_id)
            while (operation_result.status != 'Succeeded' and 
                   operation_result.status != 'Failed'):
                operation_result = self.sms.get_operation_status(self.result.request_id)
            print("Affinity Group creation {}".format(operation_result.status))
            

# A random string generator
def random_str(randomlength = 8):
    str = ''
    chars = 'abcdefghijklmnopqrstuvwxyz1234567890'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str

# Decide the user config
subscription_id = raw_input("Subscription_id: ")
certificate_path = raw_input("Certificate_path: ")
host = "management.core.chinacloudapi.cn"
storage_host = ".blob.core.chinacloudapi.cn"

# Build up a servie
sms = ServiceManagementService(subscription_id, certificate_path, host)

# Build up a cloud service
serv_list = sms.list_hosted_services()

# Here not creating a new service may lead to some troublesome namespace problems
# You can change True into len(serv_list) == 0 to avoid creating too many services

if(True):
    location = 'China East'
    ag_name = 'Wonderland'
    ag = AGroup(sms)
    ag.create()
    ag.wait_result()

    vn = VirtualNetwork(sms, ag_name=ag.name)
    vn.create()
    vn.wait_result()

    # Guarantee there is no duplicated service name
    serv_name = "thu-mooc" + random_str()
    while(not(sms.check_hosted_service_name_availability(serv_name).result)):
        serv_name = "thu-mooc" + random_str()

    label = serv_name
    desc = "auto generated service"

    result = sms.create_hosted_service(serv_name, label, desc, affinity_group=ag.name)

else:
    serv_name = serv_list[0].service_name
    print("Use cloud service " + serv_name)


# Build up a cloud storage
ac_list = sms.list_storage_accounts()

# Here not creating a new storage account may lead to some troublesome namespace problems
# You can change True into len(ac_list) == 0 to avoid creating too many storage account
if(True):
    # Guarantee the uniqueness of the name of storage account
    storage_name = 'thumooc' + random_str()
    while(not(sms.check_storage_account_name_availability(storage_name).result)):
        storage_name = 'thumooc' + random_str()
    label = 'mystorageaccount'
    desc = 'My storage account description.'
    result = sms.create_storage_account(storage_name, desc, label, affinity_group=ag.name)

    operation_result = sms.get_operation_status(result.request_id)
    print('Cloud sotrage creation operation status: ' + operation_result.status)
    while(operation_result.status != 'Succeeded'):
        operation_result = sms.get_operation_status(result.request_id)

    print('Cloud sotrage creation operation status: ' + operation_result.status)
else:
    storage_name = ac_list[0].service_name
    print("Use storage account " + storage_name)


# Create a container in the storage account
key = sms.get_storage_account_keys(storage_name).storage_service_keys.primary
blob_service = BlobService(account_name = storage_name, account_key = key, host_base = storage_host)

container_name = 'vhds'
flag = True
for container in blob_service.list_containers():
    if(container.name == container_name):
        flag = False
        print("Container already exists, skip the step!")
if(flag):
    blob_service.create_container(container_name)
    print("Create a container!")

# Copy the image into local container
flag = True
for blob in blob_service.list_blobs(container_name):
    if(blob.name == 'image.vhd'):
        flag = False

if(flag):
    blob_name = 'image.vhd'
    blob_service.copy_blob(container_name, blob_name, 'https://portalvhds7wfwtym5v2wpk.blob.core.chinacloudapi.cn/vhds/mooc-test-linx2-20140708-208615-os-2014-07-08.vhd')
else:
    print("The image already exists. Skip the copy!")

# Build up a image
name = 'mylinux'
label = 'mylinux'
os = 'Linux' # Linux or Windows
media_link = 'https://'+ storage_name + '.blob.core.chinacloudapi.cn/vhds/image.vhd'
flag = True

result = sms.list_os_images()
for image in result:
    if image.name == name:
        result = sms.delete_os_image(name)

        operation_result = sms.get_operation_status(result.request_id)
        print('Image deletion operation status: ' + operation_result.status)

result = sms.add_os_image(label, media_link, name, os)

operation_result = sms.get_operation_status(result.request_id)
print('Image creation Operation status: ' + operation_result.status)

# Build up VM
name = 'myvm' + random_str()
name_1 = name + '1'
name_2 = name + '2'

dep_name = 'myvm'

# Step 1 Select an image
image_name = 'mylinux'

# Step 2 Select destination storage account container/blob where the VM disk
# will be created


media_link_1 = 'https://' + storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_1 + '.vhd'

# Step 3 Linux VM configuration, you can use WindowsConfigurationSet
# for a Windows VM instead
linux_config_1 = LinuxConfigurationSet('host' + name_1, 'Tsinghua', 'Mooc_2014', False)


# Endpoint (port) configuration example, since documentation on this is lacking:
endpoint_config = ConfigurationSet()
endpoint_config.configuration_set_type = 'NetworkConfiguration'
endpoint1 = ConfigurationSetInputEndpoint(name='RDP', protocol='tcp', port='3389', local_port='3389', load_balanced_endpoint_set_name=None, enable_direct_server_return=False)
endpoint2 = ConfigurationSetInputEndpoint(name='SSH', protocol='tcp', port='22', local_port='22', load_balanced_endpoint_set_name=None, enable_direct_server_return=False)

endpoint_config.input_endpoints.input_endpoints.append(endpoint1)
endpoint_config.input_endpoints.input_endpoints.append(endpoint2)
endpoint_config.subnet_names.append('Subnet-1')

os_hd_1 = OSVirtualHardDisk(image_name, media_link_1)

endpoint_config.static_vip = '192.168.1.1'

print('{ip} is ready to go'.format(ip=endpoint_config.static_vip))
result = sms.create_virtual_machine_deployment(service_name=serv_name,
                                               deployment_name=dep_name,
                                               deployment_slot='production',
                                               label=name,
                                               role_name=name_1,
                                               network_config=endpoint_config,
                                               system_config=linux_config_1,
                                               os_virtual_hard_disk=os_hd_1,
                                               role_size='Medium',
                                               virtual_network_name=vn.name,
)
operation_result = sms.get_operation_status(result.request_id)
print('VM#1 creation operation status: ' + operation_result.status)
while (operation_result.status != 'Succeeded' and operation_result.status != 'Failed'):
    operation_result = sms.get_operation_status(result.request_id)
print('VM#1 creation operation status: ' + operation_result.status)

endpoint_config.input_endpoints.input_endpoints.pop()
endpoint_config.input_endpoints.input_endpoints.pop()


for i in range(2, 9):
    name_i = name + str(i)
    ip = endpoint_config.static_vip.split('.')
    ip[-1] = str(i)
    endpoint_config.static_vip = '.'.join(ip)
    print('{ip} is ready to go'.format(ip=endpoint_config.static_vip))
    media_link_i = 'https://' + storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_i + '.vhd'
    os_hd_i = OSVirtualHardDisk(image_name, media_link_i)
    linux_config_i = LinuxConfigurationSet('host' + name_i, 'Tsinghua', 'Mooc_2014', True)
    result = sms.add_role(
        service_name=serv_name,
        deployment_name=dep_name,
        role_name=name_i,
        system_config=linux_config_i,
        network_config=endpoint_config,
        os_virtual_hard_disk=os_hd_i,
        role_size='Medium'
    )
    operation_result = sms.get_operation_status(result.request_id)
    print('VM#{i} creation operation status: '.format(i=i) + operation_result.status)
    while(operation_result.status != 'Succeeded' and operation_result.status != 'Failed'):
        operation_result = sms.get_operation_status(result.request_id)
    print('VM#{i} creation operation status: '.format(i=i) +
          operation_result.status)

# result = sms.add_role(service_name=serv_name,
#     deployment_name=dep_name,
#     role_name=name_2,
#     system_config=linux_config_2,
#     os_virtual_hard_disk=os_hd_2,
#     role_size='Medium')

# operation_result = sms.get_operation_status(result.request_id)
# print('VM#2 creation operation status: ' + operation_result.status)
# while(operation_result.status != 'Succeeded'):
#     sleep(3)
#     operation_result = sms.get_operation_status(result.request_id)
    

# print('VM#2 creation operation status: ' + operation_result.status)

# Step 4 Start the created VM
# No need because it is started by default
# You may need to wait for a sec to see it starts
#sms.start_role(serv_name, name, name)
