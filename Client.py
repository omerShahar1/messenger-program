import socket
import threading
import time


def start(TCP_client, address: tuple) -> bool:
    """
    :param TCP_client: the client socket
    :param address: address (ip, port number) of the server
    :return: True if we connected to the server. False otherwise.
    """
    try:
        TCP_client.connect(address)  # connecting client to server
        return True
    except:
        print("Wrong IP or port. Try again")
        return False


def get_file(server_ip, new_port: int):
    """
    :param server_ip: the server ip adress
    :param new_port: the server new UDP socket port number
    :return: we create the client new UDP socket and use it to receive the file data from the server. once all the
    data has arrived, the function will create new file and write the data to it. The socket then will be closed.
    """
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # new UDP socket initialization
    udp_client.bind(("", 0))
    new_address = (server_ip, new_port)  # the server UDP socket address
    udp_client.sendto("test".encode(), new_address)  # send test message to the server
    data, temp_address = udp_client.recvfrom(512)  # we will receive amount of packets to expect
    size = int(data.decode())
    data_list = [""] * size  # use to store the incoming data in the correct order
    packet_check_list = [False] * size  # use to check if we had any packet loss

    while False in packet_check_list:
        data, temp_address = udp_client.recvfrom(2048)
        data_string = data.decode()
        if data_string == "status":
            index = packet_check_list.index(False)  # search what packet we didn't get
            udp_client.sendto(str(index).encode(), new_address)
            continue

        index = data_string.index(':')
        packet_number = int(data_string[:index])  # first 4 bytes are the serial number
        data_list[packet_number] = data_string[index + 1:]
        packet_check_list[packet_number] = True

    udp_client.sendto("stop".encode(), new_address)
    udp_client.close()
    print("waiting")
    new_name = input("enter file new name ")
    with open(new_name, 'w') as file:
        for i in data_list:
            file.write(i)


def receive(TCP_client, server_ip) -> None:
    """
    :param TCP_client: the client socket
    :param server_ip: IP address of the server
    :return: infinite loop to receive messages.
    """
    while True:
        try:
            message = TCP_client.recv(4096).decode()
            if message == "Disconnected":  # if that was the message then we requested to disconnect from the server
                print(message)
                TCP_client.close()
                break
            elif ':' in message:
                print(message)
            else:  # if the message didn't have ':' then we requested to download, and we need to switch to UDP
                UDP_thread = threading.Thread(target=get_file, args=(server_ip, int(message)))
                UDP_thread.start()
        except:
            print("An error occurred! Message didn't received")
            TCP_client.close()


def write(TCP_client) -> None:
    """
    :param TCP_client: the client socket
    :return: infinite loop to get the user input and send messages to the server
    """
    while True:  # message layout
        time.sleep(0.0000001)
        message: str = input()
        TCP_client.send(message.encode())


if __name__ == '__main__':
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket initialization
    client.bind(("", 0))

    while True:
        ip = input("Enter IP address of the server. (Local host address is 127.0.0.1) ")
        port = input("Enter destination port number (55000 - 55015) ")
        if start(TCP_client=client, address=(ip, int(port))):
            break

    receive_thread = threading.Thread(target=receive, args=(client, ip))  # receiving multiple messages
    receive_thread.start()
    write_thread = threading.Thread(target=write, args=(client,))  # sending messages
    write_thread.start()
