from azure import *
from azure.servicemanagement import *
from azure.storage import *
from random import Random
import time
import pickle

class AzureManage:
    def __init__(self):
        self.serv_host = 'management.core.chinacloudapi.cn'
        self.storage_host = '.blob.core.chinacloudapi.cn'
        self.location = 'China East'
        self.image_path = 'https://portalvhds7wfwtym5v2wpk.blob.core.chinacloudapi.cn/vhds/mooc-test-linx2-20140708-208615-os-2014-07-08.vhd'
        self.disk_path = 'https://portalvhds7wfwtym5v2wpk.blob.core.chinacloudapi.cn/vhds/used-for-test-used-for-test-0723-1.vhd'

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
            print("服务初始化失败！")
            print("请确认已经生成证书，并已将证书上传Azure！")
            print("请确认提供的订阅ID是正确的！")
            sub_id = raw_input("Subscription ID: ")
            self.no_config = True
            self.config['subscription_id'] = sub_id

        if self.no_config:
            self._dump_config()

    def get_hosted_service(self):
        if self.no_config or not(self.config['serv_name']):
            print("New hosted service will be created.")
            self.serv_name = 'thu-mooc' + self._random_str()
            while not(self.sms.check_hosted_service_name_availability(self.serv_name).result):
                self.serv_name = 'thu-mooc' + self._random_str()
            label = 'myhostedservice'
            desc = 'auto generated service'
            self.sms.create_hosted_service(self.serv_name, label, desc, self.location)

            self.config['serv_name'] = self.serv_name
            self._dump_config()
        else:
            self.serv_name = self.config['serv_name']

    def get_hosted_storage(self):
        if self.no_config or not(self.config['storage_name']):
            print("New storage account will be create.")
            self.storage_name = 'thu-mooc' + self._random_str()
            while not(self.sms.check_storage_account_name_availability(self.storage_name).result):
                self.storage_name = 'thu-mooc' + self._random_str()
            label = 'mystorageaccount'
            desc = 'auto generated storage account'
            result = self.sms.create_storage_account(self.storage_name, desc, label, location = self.location)
            self._wait_operand(result, 'storage_account creation')
            self.config['storage_name'] = self.storage_name
            self._dump_config()
        else:
            self.storage_name = self.config['storage_name']

        key = self.get_storage_account_keys(self.storage_name).storage_service_keys.primary
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
        name = 'myvm' + random_str()
        name_1 = name + '1'
        name_2 = name + '2'

        dep_name = 'myvm'

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
                                                            role_size = 'Medium')
        self._wait_operand(result, "VM#1 Creation")

        result = self.sms.add_role(service_name = self.serv_name,
                                   deployment_name = dep_name,
                                   role_name = name_2,
                                   system_config = linux_config_2,
                                   os_virtual_hard_disk = os_hd_2,
                                   role_size = 'Medium')
        self._wait_operand(result, "VM#2 Creation")

        # Step 4 Create a data disk and attach it to the VMs

        disk_path = 'https://' + self.storage_name + '.blob.core.chinacloudapi.cn/vhds/data_disk.vhd'

        # According to Azure doc, this is ignored when source_media_link is specified
        media_link = 'https://' + self.storage_name + '.blob.core.chinacloudapi.cn/vhds/' + name_1 + '_disk.vhd'

        result = self.sms.add_data_disk(service_name = self.serv_name,
                                        deployment_name=dep_name,
                                        role_name=name_1,
                                        lun=3,
                                        media_link=media_link,
                                        disk_label='data disk',
                                        disk_name='data_disk',
                                        host_caching='ReadOnly',
                                        source_media_link=disk_path)
        self._wait_operand(result, "Data disk attaching")


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

    def _random_str(selfrandomlength = 8):
        str = ''
        # Do NOT use capital here!
        chars = 'abcdefghijklmnopqrstuvwxyz1234567890'
        length = len(chars) - 1
        random = Random()
        for i in range(randomlength):
            str += chars[random.randint(0, length)]
        return str
