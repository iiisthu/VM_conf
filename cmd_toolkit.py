import paramiko
import pickle
from toolkit import *


class CMD:
    def __init__(self, host):
        self.account = 'Tsinghua'
        self.password = 'Mooc_2014'
        self.host = host
        self.config_template = 'Host {}\n Hostname {}\n HostKeyAlias {}\n CheckHostIP no\n Port {}\n User Tsinghua\n'
        self.config_file_path = "/Users/Joe/.ssh/config"

    def write_config(self):
        with open(self.config_file_path, 'a') as config_file:
            for i in range(1, 9):
                config_file.write(self.config_template.format(self.host + str(i), self.host, self.host + str(i), 1000 + i))

    def connect_to_VM(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname = self.host, port = 1001, username = self.account, password = self.password)
        ssh.exec_commant('sudo mkdir /mnt/data')
        ssh.exec_command('sudo mount /dev/sdc1 /mnt/data')
        ssh.close()
