import socket
import threading
import os


def find_name(client, users: dict) -> str:
    """
    :param client: socket of the current client
    :param users: dict of online users
    :return: return the name of the requested client (or "" if the client is not online)
    """
    for name in users.keys():
        if users[name] == client:
            return name
    return ""


def send_all(client, message: str, users: dict) -> None:
    """
    :param client: socket of the current client
    :param message: message the user want to send to all users
    :param users: dict of online users
    :return: if client is logged in then send the message to all online users.
    """
    try:
        name = find_name(client, users)
        if name == "":  # if the client is not in the online users' dict then the function will return "".
            client.send("SERVER: Can't send. Need to log in first".encode())
    except:
        return

    full_message = "{} (to all): {}".format(name, message).encode()
    for c in users.values():  # Send to all users
        c.send(full_message)


def send(client, message: str, target_name: str, users: dict) -> None:
    """
    :param client: socket of the current client
    :param message: message the user want to send
    :param target_name: the name of the user we will send the message to
    :param users: dict of online users
    :return: send the message to a specific user or send back fail message if the target was offline
    """
    src_name = find_name(client, users)
    try:
        if src_name == "":  # if the client is not in the online users' dict then the function will return "".
            client.send("SERVER: Can't send. Need to log in first".encode())
        elif target_name not in users.keys():
            client.send("SERVER: Can't send. Target is not logged in".encode())
        full_message = "{}: {}".format(src_name, message)
        users[target_name].send(full_message.encode())
    except:
        pass


def disconnect(client, users: dict) -> None:
    """
    :param client: socket of the current client
    :param users: dict of online users
    :return: disconnect from the server. If user was online then we will use logout first.
    """
    if client in users:
        log_out(client, users)
    try:
        client.send("SERVER: Disconnected".encode())
    except:
        pass
    finally:
        client.close()


def log_out(client, users: dict) -> None:
    """
    :param client: socket of the current client
    :param users: dict of online users
    :return: log out the user but keep the TCP connection with the server. Inform all online users about it.
    """
    name = find_name(client, users)
    try:
        if name == "":  # if the client is not in the online users' dict then the function will return "".
            client.send("SERVER: Can't log out. Need to log in first".encode())
        users.pop(name)
        client.send("SERVER: Log out".encode())
    except:
        pass

    finally:
        message = "SERVER: {} is logged out".format(name).encode()
        for c in users.values():
            c.send(message)


def log_in(client, name: str, users: dict) -> None:
    """
    :param client: socket of the current client
    :param name: name of the new client
    :param users: dict of online users
    :return: if name is legal (not empty, doesn't contain '|' and not in use) then we will combine it with
    its socket and send notice to all online users
    """
    try:
        if client in users.values():
            client.send("SERVER: Can't log in. Need to log out first".encode())
        elif name in users.keys():
            client.send("SERVER: Can't log in. Name taken".encode())
        elif name == "" or '|' in name:
            client.send("SERVER: Can't log in. Illegal name".encode())
    except:
        return

    message = "SERVER: {} is logged in".format(name).encode()
    for c in users.values():
        c.send(message)
    users[name] = client

    try:
        client.send("SERVER: Log in".encode())
    except:
        pass


def download(client, file_name: str, users: dict) -> None:
    """
    :param users: dict of online users
    :param client: socket of the current client
    :param file_name: name of the file
    :return: If file exist, we create new UDP socket with unused port, send notice to the client and start sending file.
    After sending the file we send message with the last byte of the file.
    If not exist then we send 'File not found' message.
    """
    try:
        if client not in users.values():
            client.send("SERVER: Can't download. Need to log in first".encode())
            return
    except:
        return

    file = "files/" + file_name
    if os.path.isfile(file):
        UDP_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP socket initialization
        UDP_server.bind(('', 0))
        port = UDP_server.getsockname()[1]
        client.send("{}".format(port).encode())
        ans = send_file(file_name=file, UDP_server=UDP_server)
        try:
            client.send("SERVER: finish download of file. Last byte is: {}".format(ans).encode())
        except:
            return

    try:
        client.send("SERVER: Can't download. File not found".encode())
    except:
        pass


def send_file(file_name, UDP_server) -> bytes:
    """
    :param file_name: name of the file
    :param UDP_server: the new UDP socket of the server
    :return: receive test message from the client UDP Socket and then save all file data in packet list with sequence
    numbers. We send amount of expected packets and wait for response. We then send the file data to the client.
    If client received all the data we will finish and close the UDP socket. Otherwise, we resend lost packets.
    Return the last byte from the file.
    """
    buff = 2048  # size of each packet sent
    i = 0  # sequence number
    data_list = []
    last_byte = b'0'

    with open(file_name, "r") as file:  # saving file data in a list of bytes representing the packets
        while True:
            data = file.read(buff - 4)  # first 4 bytes are used as sequence number
            if not data:  # if we finished reading the file
                break
            data_list.append((str(i) + ":" + data).encode())
            i += 1

    while True:
        data, client_address = UDP_server.recvfrom(512)  # test message from the client
        UDP_server.sendto(str(len(data_list)).encode(), client_address)  # we send the amount of packets we need
        break

    for data in data_list:  # send file data
        UDP_server.sendto(data, client_address)
        last_byte = data[-1]

    while True:
        UDP_server.sendto("status".encode(), client_address)
        data, temp_address = UDP_server.recvfrom(512)  # will be the order to stop or a packet number to resend
        message = data.decode()
        if message == "stop":  # if the client confirm receiving all the file data then stop
            print("finish sending file")
            UDP_server.close()
            return last_byte
        index = int(data.decode())
        UDP_server.sendto(data_list[index], client_address)
        last_byte = data_list[index][-1]


def show_users(client, users: dict) -> None:
    """
    :param client: socket of the current client
    :param users: dict of online users
    :return: send back list of online users (the names).
    """
    try:
        client.send("SERVER: online users: {}".format(users.keys().__repr__()).encode())
    except:
        pass


def show_files(client) -> None:
    """
    :param client: socket of the current client
    :return: send back list of files (the names)
    """
    files = []
    for filename in os.listdir("files"):
        files.append(filename)

    try:
        client.send("SERVER: files: {}".format(files.__str__()).encode())
    except:
        pass


def handle(users: dict, client, client_address: tuple) -> None:
    """
    :param client_address: the address of the current client (ip, port)
    :param users: dict of online users
    :param client: socket of the current client
    :return: receive the messages from a given client in an infinite loop and select the correct action we need to take.
    If the client is closed (disconnection for example) the client will be closed and the loop will stop.
    """
    while True:
        try:  # receiving valid messages from client
            message: str = client.recv(2048).decode()
            if message[:7] == "log_in|":
                log_in(client=client, name=message[7:], users=users)
            elif message == "disconnect":
                disconnect(client=client, users=users)
                print("Client from {} is disconnected".format(client_address))
                break
            elif message == "show_users":
                show_users(client=client, users=users)
            elif message == "show_files":
                show_files(client=client)
            elif message[:9] == "download|":
                download(client=client, file_name=message[9:], users=users)
            elif message[:5] == "send|":
                s = message.split('|')
                if len(s) == 2:
                    send_all(client=client, message=s[1], users=users)
                elif len(s) == 3:
                    send(client=client, target_name=s[1], message=s[2], users=users)
                else:
                    client.send("SERVER: Illegal command. Try again.".encode())
            else:
                client.send("SERVER: Illegal command. Try again.".encode())

        except:  # removing clients
            disconnect(client, users)
            print("Client from {} is disconnected".format(client_address))
            break


def connect(TCP_server, users: dict, server_port: int) -> None:  # accepting multiple clients
    """
    :param server_port: the server port of the current socket
    :param TCP_server: the server socket
    :param users: list of online users
    :return: accept connection request from the client and open a new thread for him
    """
    while True:
        client, address = TCP_server.accept()
        print("IP: {} is connected from port: {} to server port: {}".format(str(address[0]), str(address[1]), server_port))
        thread = threading.Thread(target=handle, args=(users, client, address))
        thread.start()


if __name__ == '__main__':
    online_users = {}  # key is the name. value is the client socket

    for i in range(55000, 55016):
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket initialization
        tcp_socket.bind(("", i))
        tcp_socket.listen(15)
        thread = threading.Thread(target=connect, args=(tcp_socket, online_users, i))
        thread.start()
