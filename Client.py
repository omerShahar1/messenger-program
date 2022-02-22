from socket import *
import threading

client = socket(AF_INET, SOCK_STREAM)  # socket initialization
address = None

while True:  # Client try to connect itself to the server
    ip_adress = input("Enter IP address of the server. (Local host address is 127.0.0.1)")
    port = input("Enter destination port number (55000 - 55015)")
    address = (ip_adress, int(port))
    try:
        client.connect(address)  # connecting client to server
        break  # Once we establish a connection we will continue.
    except:
        print("Wrong IP or port. Try again")

udp_client = socket(AF_INET, SOCK_DGRAM)
udp_client.settimeout(30)


def get_file(new_port: int, new_name: str):
    new_address = ("127.0.0.1", new_port)  # the server UDP socket address
    udp_client.sendto("1".encode(), new_address)  # send message to the server, so it will have the client new address
    data, temp_address = udp_client.recvfrom(65535)  # we will receive amount of packets to expect
    size = int(data.decode())
    data_list = [""] * size  # use to store the incoming data in the correct order
    packet_check_list = [False] * size  # use to check if we had any packet loss

    while False in packet_check_list:
        data, temp_address = udp_client.recvfrom(65535)
        data_string = data.decode()
        if data_string == "status":
            i = packet_check_list.index(False)
            udp_client.sendto(str(i).encode(), new_address)
            continue
        index = data_string.find(":")
        if index == -1:  # if nothing was received then try again
            continue

        packet_number = int(data_string[:index])
        data_list[packet_number] = data_string[(index + 1):]
        packet_check_list[packet_number] = True

    udp_client.sendto("stop".encode(), new_address)

    print("finish downloading. Last digits are: ")
    with open(new_name, 'w') as file:
        for i in data_list:
            file.write(i)


def receive():
    while True:  # making valid connection
        try:
            message = client.recv(4096).decode()
            if message[0] == "1":
                new_name = input("Enter the file new name")
                get_file(int(message[1:]), new_name)  # The received message will contain the new UDP server-port
            else:
                print(message[1:])
        except:
            print("An error occurred! Message didn't received")


def write():
    while True:  # message layout
        message: str = input()
        client.send(message.encode())


receive_thread = threading.Thread(target=receive)  # receiving multiple messages
receive_thread.start()
write_thread = threading.Thread(target=write)  # sending messages
write_thread.start()
