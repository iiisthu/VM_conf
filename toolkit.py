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
        self.image_path = 'https://portalvhds7wfwtym5v2wpk.blob.core.chinacloudapi.cn/vhds/mooc-test-linx2-20140708-208615-os-2014-07-08.vhd'
        self.disk_path = 'https://portalvhds7wfwtym5v2wpk.blob.core.chinacloudapi.cn/vhds/used-for-test-used-for-test-0723-1.vhd'

        self.no_conf = False
        try:
            with open('user_config', 'rb') as conf_file:
                self.config = pickle.load(conf_file)
        except IOError as err:
            print("No config file. Will be created.")
            sub_id = raw_input("Subscription ID: ")
            self.config = {'subscription_id' : sub_id, 'certificate_path' : './cert.pem'}
            self.no_conf = True
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
            self.config['subscription_id'] = sub_id

        if self.no_conf:
            try:
                with open('user_config', 'wb') as conf_file:
                    pickle.dump(self.config, conf_file)
            except IOError as err:
                print("File error: " + str(err))
            except pickle.PickleError as perr:
                print("Pickle error: " + str(perr))

    def
