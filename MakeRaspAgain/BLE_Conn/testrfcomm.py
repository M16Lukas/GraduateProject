import bluetooth
import signal
import sys
import subprocess

HOST = ""
PORT = bluetooth.PORT_ANY
UUID = "4a4ece60-7eb0-11e4-b4a9-0800200c9a66"

def signal_handler(sig, frame):
    try:
        connected_socket.close()
    except:
        pass
    
    server_socket.close()
    sys.exit()
    
signal.signal(signal.SIGINT, signal_handler)

server_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
server_socket.bind((HOST,PORT))
server_socket.listen(5)

port = server_socket.getsockname()[1]
print("port : ", port)

bluetooth.advertise_service(
    server_socket,
    name="server",
    service_id=UUID,
    service_classes=[UUID, bluetooth.SERIAL_PORT_CLASS],
    profiles=[bluetooth.SERIAL_PORT_PROFILE],
)

try:
    while True:
        connected_socket, client_address = server_socket.accept()
        data = connected_socket.recv(1024)
        print("client : ", data)
        connected_socket.send(data)
except:
    pass

connected_socket.close()
server_socket.close()