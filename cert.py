import os
os.system("openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout cert.pem -out cert.pem")
os.system("openssl x509 -inform pem -in cert.pem -outform der -out cert.cer")
