import bluetooth
import subprocess
import time
import threading

thread_flag = True

class ServerThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        
    def run(self):
        server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        port = bluetooth.PORT_ANY
        server_socket.bind(("",port))
        server_socket.listen(5)
        
        while thread_flag:
                client_socket, address = server_socket.accept()
                print("Accepted ", address)
                serviceThread = ServiceThread(client_socket, address)
                serviceThread.start()
            
        server_socket.close()
        client_socket.close()

class ServiceThread(threading.Thread):
    def __init__(self, client_socket, address):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.address = address
        
    def run(self):
        sendThread = SendThread(self.client_socket, self.address)
        sendThread.start()
        
        while thread_flag:
            data = self.client_socket.recv(1024)
            print("Received : %s" % data)
            
            if (data == 'q'):
                print("Quit")
                break
            
            data_split=data.split(",*,")
            
            if len(data_split) == 2:
                ssid = data_split[0]
                password = data_split[1]
                
                print("SSID Receive : " + ssid)
                print("Password Receive : " + password)
                print("Make connect...")
                
                f = open("/etc/wpa_supplicant/wpa_supplicant.conf", 'w')
                f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
                f.write("update_config=1\n")
                f.write("country=US\n")
                f.write("\n")
                f.write("network={\n")
                f.write("\tssid=\""+ssid+"\"\n")
                f.write("\tpsk=\""+password+"\"\n")
                f.write("\tkey_mgmt=WPA-PSK\n")
                f.write("}\n")
                f.close()
                
                subprocess.call(["sudo","ifdown","wlan0"])
                subprocess.call(["sudo","ifconfig","wlan0","down"])
                time.sleep(3)
                subprocess.call(["sudo","ifup","wlan0"])
                subprocess.call(["sudo","ifconfig","wlan0","up"])
            elif len(data_split) == 3:
                global MY_MAJOR, MY_MINOR
                MY_MAJOR = data_split[0]
                MY_MINOR = data_split[1]
                f = open("/etc/MakeKPUAgain.conf", 'w')
                f.wrtie(MY_UUID + "\n")
                f.wrtie(MY_MAJOR + "\n")
                f.wrtie(MY_MINOR + "\n")
                f.close()
                print("----- Conf changed: ", MY_MAJOR, ", ", MY_MINOR, "-----")
            elif data_split[0] == 'wifi':
                subprocess.call(["sudo","ifup","wlan0"])
                subprocess.call(["sudo","ifconfig","wlan0","up"])
                try:
                    result = subprocess.check_output(["sudo","iwlist","wlan0","scan"])
                    result_split = result.splitlines()
                    result_final = ''
                    for item in result_split:
                        if 'ESSID' in item:
                            result_final = result_final + item.strip()
                    result_final = result_final.strip()
                    result_final_split = result_final.split("ESSID:")
                    massage = ""
                    for item in result_final_split:
                        if item != '':
                            message = message + item[1:-1] + ','
                    if len(message) > 0:
                        message = message[:-1]
                except subprocess.CalledProcessError as e:
                    print(e.output)
                
                print(message)
                self.client_socket.send(message)
        
        self.client_socket.close()
                
class SendThread(threading.Thread):
    def __init__(self, client_socket, addr):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.address = addr
    
    def run(self):
        while thread_flag:
            try:
                result = subprocess.check_output(["ifconfig", "wlan0"])
                if 'inet' in result:
                    self.client_socket.send("wifion")
                else:
                    self.client_socket.send("wifioff")
                
                time.sleep(2)
            except subprocess.CalledProcessError as e:
                print(e.output)
        self.client_socket.close()
        
serverThread = ServerThread()
while True:
    serverThread.start()