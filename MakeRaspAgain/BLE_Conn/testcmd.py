import bluetooth
import subprocess
import time
import threading

server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
port = 1
server_socket.bind(("",port))
server_socket.listen(5)

client_socket, address = server_socket.accept()
print("Accepted ", address)

client_socket.close()
server_socket.close()

