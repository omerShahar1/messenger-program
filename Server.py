import time
from socket import *
import threading
import os

port = 55000
udp_port = 5005
users = []
users_names = []

server = socket(AF_INET, SOCK_STREAM)  # TCP socket initialization
server.bind(("", port))  # Binding any host and a specific port to socket
udp_server = socket(AF_INET, SOCK_DGRAM)  # UDP socket initialization
udp_server.bind(("", udp_port))  # Binding any host and a specific port to socket
server.listen(15)


def broadcast_all(client, message: str):  # broadcast to all users
    if client not in users:
        client.send("0Broadcast failed. You are offline".encode())
        return

    index = users.index(client)
    name = users_names[index]
    full_message = "0(to all) " + name + ": " + message  # '0' is for the client to understand we continue with TCP
    for c in users:  # Send to all online users
        c.send(full_message.encode())


def broadcast(client, message: str, target_name: str):  # broadcast to a specific user
    if client not in users:
        client.send("0Broadcast failed. You are offline".encode())
        return
    if target_name not in users_names:
        client.send("0Broadcast failed. Target is offline".encode())
        return

    src_index = users.index(client)
    name = users_names[src_index]
    full_message = "0" + name + ": " + message  # '0' is for the client to understand we continue with TCP
    target_index = users_names.index(target_name)
    users[target_index].send(full_message.encode())


def disconnect(client):
    if client not in users:
        client.send("0Disconnection failed. You were not connected".encode())
        return

    index = users.index(client)
    users.remove(client)
    name = users_names.pop(index)
    client.send("0Disconnected".encode())

    for c in users:
        c.send("0{} is disconnected".format(name).encode())
    print("{} is disconnected".format(name))


def download(client, file_name: str):
    file = "files/" + file_name
    if os.path.isfile(file):  # we send message to inform the client to use UDP, and we send the server UDP port number
        client.send("1{}".format(udp_port).encode())
        send_file(file)
    else:
        client.send("0File not found".encode())


def send_file(file_name):
    time.sleep(0.002)
    temp_data, new_address = udp_server.recvfrom(1024)
    data_list = []
    with open(file_name, "r") as file:
        while True:
            data = file.read(4096)
            if data == "":
                break
            data_list.append(data)

    udp_server.sendto(str(len(data_list)).encode(), new_address)  # we send the amount of packets we need
    i = 0
    for data in data_list:
        udp_server.sendto((str(i) + ":" + data).encode(), new_address)
        i += 1

    while True:
        udp_server.sendto("status".encode(), new_address)
        data, temp_address = udp_server.recvfrom(65535)
        if data.decode() == "stop":
            break
        i = int(data.decode())
        udp_server.sendto((str(i) + ":" + data_list[i]).encode(), new_address)
    print("finish sending file")


def connect(client, name: str):
    if client in users:
        client.send("0Connection failed. You are already online".encode())
        return
    if name in users_names:
        client.send("0Connection failed. Name already taken.".encode())
        return
    users_names.append(name)
    users.append(client)
    client.send('0Connected'.encode())
    for c in users:
        c.send("0{} is connected".format(name).encode())
    print("{} is connected".format(name))


def get_users(client):
    client.send(("0" + users_names.__str__()).encode())


def get_list_files(client):
    files = []
    for filename in os.listdir("files"):
        files.append(filename)
    client.send(("0" + files.__str__()).encode())


def handle(client, address):
    while True:
        try:  # receiving valid messages from client
            message: str = client.recv(1024).decode()
            s = message.split("|")
            if len(s) == 1 and s[0] == "disconnect":
                disconnect(client)
            elif len(s) == 1 and s[0] == "get_users":
                get_users(client)
            elif len(s) == 1 and s[0] == "get_list_files":
                get_list_files(client)
            elif len(s) == 2 and s[0] == "connect":
                connect(client, s[1])
            elif len(s) == 2 and s[0] == "download":
                download(client, s[1])
            elif len(s) == 2 and s[0] == "send":
                broadcast_all(client, s[1])
            elif len(s) == 3 and s[0] == "send":
                broadcast(client, s[1], s[2])
            else:
                client.send("Illegal command. Try again".encode())

        except:  # removing clients
            if client in users:
                index = users.index(client)
                users.remove(client)
                client.close()
                name = users_names.pop(index)
                for c in users:
                    c.send("0{} is disconnected".format(name).encode())
                print("{} is disconnected".format(name))
                print("Host {} is disconnected".format(address[0]))
                break
            client.close()
            print("Host {} is disconnected".format(address[0]))
            break


def receive():  # accepting multiple clients
    while True:
        client, address = server.accept()
        print("Connected with {}".format(str(address[0])))
        thread = threading.Thread(target=handle, args=(client, address))
        thread.start()


receive()
