from azure import *
from azure.servicemanagement import *
from azure.storage import *
from random import Random

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
    # It seems that there is no need to choose the location.
    # The default location will be China East.
    # You can change it by uncommending the following piece of code
    # or you can change the location directly.
    # Note only China East and China North are supported.
    '''
    result = sms.list_locations()
    for location in result:
        print(location.name)

    location = raw_input("Select a location: ")
    '''
    location = 'China East'

    # Guarantee there is no duplicated service name
    serv_name = "thu-mooc" + random_str()
    while(not(sms.check_hosted_service_name_availability(serv_name).result)):
        serv_name = "thu-mooc" + random_str()

    label = serv_name
    desc = "auto generated service"

    result = sms.create_hosted_service(serv_name, label, desc, location)
else:
    serv_name = serv_list[0].service_name
    print("Use cloud service " + serv_name)

# Old-versioned code
'''
operation_result = sms.get_operation_status(result.request_id)
print("Cloud service creation operation status: " + operation_result.status)
'''

'''
flag = True

result = sms.list_hosted_services()
for service in result:
    if service.service_name == name:
        flag = False
if(flag):
    result = sms.create_hosted_service(name, label, desc, location)

    operation_result = sms.get_operation_status(result.request_id)
    print("Cloud service creation operation status: " + operation_result.status)
else:
    print("Cloud service already exists, skip the step!")
'''

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
    result = sms.create_storage_account(storage_name, desc, label, location=location)

    operation_result = sms.get_operation_status(result.request_id)
    print('Cloud sotrage creation operation status: ' + operation_result.status)
    while(operation_result.status != 'Succeeded'):
        operation_result = sms.get_operation_status(result.request_id)

    print('Cloud sotrage creation operation status: ' + operation_result.status)
else:
    storage_name = ac_list[0].service_name
    print("Use storage account " + storage_name)

# Old-versioned code
'''
flag = True
result = sms.list_storage_accounts()
for account in result:
    if(account.service_name == name):
        flag = False

if(flag):
    result = sms.create_storage_account(name, desc, label, location=location)

    operation_result = sms.get_operation_status(result.request_id)
    print('Cloud sotrage creation operation status: ' + operation_result.status)
else:
    print("Cloud storage already exists, skip the step!")


result = sms.create_storage_account(storage_name, desc, label, location=location)

operation_result = sms.get_operation_status(result.request_id)
print('Cloud sotrage creation operation status: ' + operation_result.status)
while(operation_result.status != 'Succeeded'):
    operation_result = sms.get_operation_status(result.request_id)

print('Cloud sotrage creation operation status: ' + operation_result.status)
'''

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
'''
result = sms.list_os_images()
for image in result:
    print(image.name)
image_name = raw_input("Select the image: ")
'''
image_name = 'mylinux'

# Step 2 Select destination storage account container/blob where the VM disk
# will be created
'''
result = sms.list_storage_accounts()
for acount in result:
    print("Service name: " + account.service_name)
    print("")
'''
media_link_1 = 'https://' + storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_1 + '.vhd'
media_link_2 = 'https://' + storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_2 + '.vhd'

# Step 3 Linux VM configuration, you can use WindowsConfigurationSet
# for a Windows VM instead
linux_config_1 = LinuxConfigurationSet('host' + name_1, 'Tsinghua', 'Mooc_2014', True)
linux_config_2 = LinuxConfigurationSet('host' + name_2, 'Tsinghua', 'Mooc_2014', True)

# Endpoint (port) configuration example, since documentation on this is lacking:
endpoint_config = ConfigurationSet()
endpoint_config.configuration_set_type = 'NetworkConfiguration'
endpoint1 = ConfigurationSetInputEndpoint(name='RDP', protocol='tcp', port='3389', local_port='3389', load_balanced_endpoint_set_name=None, enable_direct_server_return=False)
endpoint2 = ConfigurationSetInputEndpoint(name='SSH', protocol='tcp', port='22', local_port='22', load_balanced_endpoint_set_name=None, enable_direct_server_return=False)

endpoint_config.input_endpoints.input_endpoints.append(endpoint1)
endpoint_config.input_endpoints.input_endpoints.append(endpoint2)

os_hd_1 = OSVirtualHardDisk(image_name, media_link_1)
os_hd_2 = OSVirtualHardDisk(image_name, media_link_2)

result = sms.create_virtual_machine_deployment(service_name=serv_name,
    deployment_name=dep_name,
    deployment_slot='production',
    label=name_1,
    role_name=name_1,
    network_config=endpoint_config,
    system_config=linux_config_1,
    os_virtual_hard_disk=os_hd_1,
    role_size='Medium')

operation_result = sms.get_operation_status(result.request_id)
print('VM#1 creation operation status: ' + operation_result.status)
while(operation_result.status != 'Succeeded'):
    operation_result = sms.get_operation_status(result.request_id)

print('VM#1 creation operation status: ' + operation_result.status)

# Not working
'''
sms.create_virtual_machine_deployment(service_name=serv_name,
    deployment_name=name_2,
    deployment_slot='production',
    label=name_2,
    role_name=name_2,
    system_config=linux_config_2,
    os_virtual_hard_disk=os_hd_2,
    role_size='Medium')
'''

result = sms.add_role(service_name=serv_name,
    deployment_name=dep_name,
    role_name=name_2,
    system_config=linux_config_2,
    os_virtual_hard_disk=os_hd_2,
    role_size='Medium')

operation_result = sms.get_operation_status(result.request_id)
print('VM#2 creation operation status: ' + operation_result.status)
while(operation_result.status != 'Succeeded'):
    operation_result = sms.get_operation_status(result.request_id)

print('VM#2 creation operation status: ' + operation_result.status)

# Step 4 Start the created VM
# No need because it is started by default
# You may need to wait for a sec to see it starts
#sms.start_role(serv_name, name, name)
