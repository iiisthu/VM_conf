from azure import *
from azure.servicemanagement import *
from azure.storage import *
from random import Random
import time
import pickle

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

class AzureManage:
    def __init__(self, get_conf, set_conf):
        self.serv_host = 'management.core.chinacloudapi.cn'
        self.storage_host = '.blob.core.chinacloudapi.cn'
        self.location = 'China East'
        self.image_path = 'https://portalvhds7wfwtym5v2wpk.blob.core.chinacloudapi.cn/vhds/mooc-test-linx2-20140708-208615-os-2014-07-08.vhd'
        self.disk_path = 'https://portalvhds7wfwtym5v2wpk.blob.core.chinacloudapi.cn/vhds/used-for-test-used-for-test-0723-1.vhd'

        # self._load_conf = get_conf
        # self._dump_conf = set_conf

        self.no_config = False
        try:
            with open('user_config', 'rb') as conf_file:
                self.config = pickle.load(conf_file)
        except IOError as err:
            print("No config file. Will be created.")
            sub_id = raw_input("Subscription ID: ")
            self.config = {'subscription_id' : sub_id,
                           'certificate_path' : './cert.pem',
                           'serv_name' : False,
                           'storage_name' : False}
            self.no_config = True
        except pickle.PickleError as perr:
            print("Pickle error: " + str(perr))

        try:
            self.sms = ServiceManagementService(self.config['subscription_id'],
                                                self.config['certificate_path'],
                                                self.serv_host)
        except:
            print("Service initialize failed!")
            print("Please make sure the certificate is generated and uploaded!")
            print("Please make sure the subscription ID is correct!")
            sub_id = raw_input("Subscription ID: ")
            self.no_config = True
            self.config['subscription_id'] = sub_id

        if self.no_config:
            self._dump_config()

    def get_hosted_service(self):
        location = 'China East'
        ag_name = 'Wonderland'
        self.ag = AGroup(self.sms)
        self.ag.create()
        self.ag.wait_result()
        self.vn = VirtualNetwork(self.sms, ag_name=self.ag.name)
        self.vn.create()
        self.vn.wait_result()
        if self.no_config or not(self.config['serv_name']) or self.sms.check_hosted_service_name_availability(self.config['serv_name']).result:
            print("New hosted service will be created.")
            self.serv_name = 'thu-mooc' + self._random_str()
            while not(self.sms.check_hosted_service_name_availability(self.serv_name).result):
                self.serv_name = 'thu-mooc' + self._random_str()
            label = 'myhostedservice'
            desc = 'auto generated service'
            self.sms.create_hosted_service(self.serv_name, label, desc, affinity_group=self.ag.name)

            self.config['serv_name'] = self.serv_name
            self._dump_config()
        else:
            self.serv_name = self.config['serv_name']

    def get_hosted_storage(self):
        if self.no_config or not(self.config['storage_name']) or self.sms.check_storage_account_name_availability(self.config['storage_name']).result:
            print("New storage account will be create.")
            self.storage_name = 'thumooc' + self._random_str()
            while not(self.sms.check_storage_account_name_availability(self.storage_name).result):
                self.storage_name = 'thumooc' + self._random_str()
            label = 'mystorageaccount'
            desc = 'auto generated storage account'
            result = self.sms.create_storage_account(self.storage_name, desc, label, affinity_group = self.ag.name)
            self._wait_operand(result, 'storage_account creation')
            self.config['storage_name'] = self.storage_name
            self._dump_config()
        else:
            self.storage_name = self.config['storage_name']

        key = self.sms.get_storage_account_keys(self.storage_name).storage_service_keys.primary
        self.blob_service = BlobService(account_name = self.storage_name,
                                        account_key = key,
                                        host_base = self.storage_host)

    def get_container(self):
        container_name = 'vhds'
        flag = True
        for container in self.blob_service.list_containers():
            if container.name == container_name:
                flag = False
                print('Container already exists, skip the creation!')
        if flag:
            self.blob_service.create_container(container_name)

    def copy_image(self):
        blob_name = 'image.vhd'
        container_name = 'vhds'
        flag = True
        for blob in self.blob_service.list_blobs(container_name):
            if blob.name == blob_name:
                flag = False
        if flag:
            blob_name = blob_name
            self.blob_service.copy_blob(container_name, blob_name, self.image_path)
        else:
            print("Image already exists. Skip the copy.")

    def copy_disk(self):
        blob_name = 'data_disk.vhd'
        container_name = 'vhds'
        flag = True
        for blob in self.blob_service.list_blobs(container_name):
            if blob.name == blob_name:
                flag = False
        if flag:
            blob_name = blob_name
            self.blob_service.copy_blob(container_name, blob_name, self.disk_path)
        else:
            print("Disk already exists. Skip the copy.")

    def register_image(self):
        name = 'mylinux'
        label = 'mylinux'
        os = 'Linux' # Linux or Windows
        media_link = 'https://'+ self.storage_name + '.blob.core.chinacloudapi.cn/vhds/image.vhd'

        result = self.sms.list_os_images()
        for image in result:
            if image.name == name:
                result = self.sms.delete_os_image(name)

                self._wait_operand(result, 'Image deletion')

        result = self.sms.add_os_image(label, media_link, name, os)
        self._wait_operand(result, 'Image creation')

    def build_VM(self):
        if(not(self.config['deletion'])):
            self.delete_roles()

        name = 'myvm' + self._random_str()
        name_1 = name + '1'
        name_2 = name + '2'

        dep_name = name
        self.config['dep_name'] = dep_name
        self.config['vm_name_1'] = name_1
        self.config['vm_name_2'] = name_2
        self._dump_config()

        # Step 1 Select an image
        image_name = 'mylinux'

        # Step 2 Select destination storage account container/blob where the VM disk
        # will be created
        media_link_1 = 'https://' + self.storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_1 + '.vhd'
        media_link_2 = 'https://' + self.storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_2 + '.vhd'


        # Step 3 Linux VM configuration, you can use WindowsConfigurationSet
        # for a Windows VM instead
        linux_config_1 = LinuxConfigurationSet('host' + name_1, 'Tsinghua', 'Mooc_2014', False)
        linux_config_2 = LinuxConfigurationSet('host' + name_2, 'Tsinghua', 'Mooc_2014', False)

        # Endpoint (port) configuration example, since documentation on this is lacking:
        endpoint_config = ConfigurationSet()
        endpoint_config.configuration_set_type = 'NetworkConfiguration'
        endpoint1 = ConfigurationSetInputEndpoint(name='RDP', protocol='tcp', port='3389', local_port='3389', load_balanced_endpoint_set_name=None, enable_direct_server_return=False)
        endpoint2 = ConfigurationSetInputEndpoint(name='SSH', protocol='tcp', port='22', local_port='22', load_balanced_endpoint_set_name=None, enable_direct_server_return=False)

        endpoint_config.input_endpoints.input_endpoints.append(endpoint1)
        endpoint_config.input_endpoints.input_endpoints.append(endpoint2)
        endpoint_config.subnet_names.append('Subnet-1')

        endpoint_config.static_vip = '192.168.1.1'

        # Virtual hard disk config
        os_hd_1 = OSVirtualHardDisk(image_name, media_link_1)
        os_hd_2 = OSVirtualHardDisk(image_name, media_link_2)

        result = self.sms.create_virtual_machine_deployment(service_name = self.serv_name,
                                                            deployment_name = dep_name,
                                                            deployment_slot = 'production',
                                                            label = name_1,
                                                            role_name = name_1,
                                                            network_config = endpoint_config,
                                                            system_config = linux_config_1,
                                                            os_virtual_hard_disk = os_hd_1,
                                                            role_size = 'Medium',
                                                            virtual_network_name=self.vn.name)
        self._wait_operand(result, "VM#1 Creation")
        
        endpoint_config.input_endpoints.input_endpoints.pop()
        endpoint_config.input_endpoints.input_endpoints.pop()

        for i in range(2, 9):
            name_i = name + str(i)
            ip = endpoint_config.static_vip.split('.')
            ip[-1] = str(i)
            endpoint_config.static_vip = '.'.join(ip)
            print('{ip} is ready to go'.format(ip=endpoint_config.static_vip))
            media_link_i = 'https://' + self.storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_i + '.vhd'
            os_hd_i = OSVirtualHardDisk(image_name, media_link_i)
            linux_config_i = LinuxConfigurationSet('host' + name_i, 'Tsinghua', 'Mooc_2014', True)
            result = self.sms.add_role(
                service_name=self.serv_name,
                deployment_name=dep_name,
                role_name=name_i,
                system_config=linux_config_i,
                network_config=endpoint_config,
                os_virtual_hard_disk=os_hd_i,
                role_size='Medium'
            )
            self._wait_operand(result, "VM#{} Creation".format(i))

            pdb.set_trace()

        # Step 4 Create a data disk and attach it to the VMs

        disk_path = 'https://' + self.storage_name + '.blob.core.chinacloudapi.cn/vhds/data_disk.vhd'

        # According to Azure doc, this is ignored when source_media_link is specified
        media_link = 'https://' + self.storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_1 + '_disk.vhd'

        result = self.sms.add_data_disk(service_name = self.serv_name,
                                        deployment_name=dep_name,
                                        role_name=name_1,
                                        lun=0,
                                        media_link=media_link,
                                        disk_label='data disk',
                                        disk_name='data_disk',
                                        host_caching='ReadOnly',
                                        source_media_link=disk_path)
        self._wait_operand(result, "Data disk attaching")

        self.config['deletion'] = False
        self._dump_config()

    def delete_roles(self):
        result = self.sms.delete_role(self.config['serv_name'],
                                      self.config['dep_name'],
                                      self.config['vm_name_1'])
        self._wait_operand(result, 'VM#1 deletion')

        result = self.sms.delete_deployment(self.config['serv_name'],
                                            self.config['dep_name'])
        self._wait_operand(result, 'VM#2 deletion')
        self.config['deletion'] = True
        self._dump_config()

    def delete_os_images(self):
        result = self.sms.delete_os_image('mylinux', True)
        self._wait_operand(result, 'OS image deletion')

    def delete_disks(self):
        for disk in self.sms.list_disks():
            if(disk.os == u'Linux'):
                result = self.sms.delete_disk(disk.name, True)
                #self._wait_operand(result, disk.name + 'Deletion')

    def _wait_operand(self, result, pro_name):
        status = 'Unknown'
        timeout = 0
        while status != 'Succeeded' and status != 'Failed' and timeout < 30:
            time.sleep(1)
            timeout = timeout + 1
            status = self.sms.get_operation_status(result.request_id).status
            print("Procedure " + pro_name +" status: " + status)

    def _dump_config(self):
        try:
            with open('user_config', 'wb') as conf_file:
                pickle.dump(self.config, conf_file)
        except IOError as err:
            print("File error: " + str(err))
        except pickle.PickleError as perr:
            print("Pickle error: " + str(perr))

    def _random_str(self, randomlength = 8):
        str = ''
        # Do NOT use capital here!
        chars = 'abcdefghijklmnopqrstuvwxyz1234567890'
        length = len(chars) - 1
        random = Random()
        for i in range(randomlength):
            str += chars[random.randint(0, length)]
        return str
