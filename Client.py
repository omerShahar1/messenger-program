import socket
import sys
import threading
import time


class Globals:
    def __init__(self):
        self.in_download = False


def start(TCP_client) -> None:
    """
    receive input of the client Ip address and the server Ip and port address. connect
    the client to the server via tcp (infinite loop until connection establish).
    :param TCP_client: the client tcp socket
    :return:
    """
    while True:
        client_ip = input("Enter client IP address (Local host address is 127.0.0.1) --> ")
        ip = input("Enter server IP address. (Local host address is 127.0.0.1) --> ")
        port = input("Enter destination port number (55000 - 55015) --> ")
        try:
            TCP_client.bind((client_ip, 0))
            TCP_client.connect((ip, int(port)))  # connecting client to server
            return
        except socket.error:
            print("One or more of the inputs were wrong. Try again")
            continue


def get_file(TCP_client, size: int, glo) -> None:
    """
    we create new UDP socket and send the port number to the server (via tcp).
    we then create list to store the data in and a boolean list to store the boolean value of each packet (if we
    received a specific packet then its sequence number will represent the location in the list and the boolean list
    cell will be true). while receiving packets we make sure that the 'stop udp' value is false. this is the boolean
    that sign we download 20% of the file and if is change to be True then the download should stop. if we have
    TimeOutError problem (a packet got lost, and we still wait for it) then we will send string of all the packets we
    still need to receive. If we got all the packets we send back to the server 'stop' command via tcp. After that we
    get input of the file new name and save the data in this file. In addition, the socket set for time of 100
    milliseconds. if we see that the socket reached TimeoutError but no new packets were received then we increase the
    socket time (that way we solve the latency problem)
    :param glo: we store here global data from all threads to read.
    :param TCP_client: the client tcp socket
    :param size: amount of packets to be received
    :return:
    """
    UDP_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # new UDP socket initialization
    UDP_client.bind((TCP_client.getsockname()[0], 0))  # bind the socket
    TCP_client.send("{}|{}".format(UDP_client.getsockname()[0], UDP_client.getsockname()[1]).encode())
    data_list = [""] * size  # use to store the incoming data in the correct order
    packet_check_list = [False] * size  # use to check if we had any packet loss
    timer = 100  # time until TimeoutError
    count = 0  # count how many packets arrived in the current run (until TimeoutError)
    count_total = 0  # count the total amount of packets we received.
    UDP_client.settimeout(timer)
    check_proceed: bool = True

    while False in packet_check_list:  # run until all packets arrived
        try:
            data, temp_address = UDP_client.recvfrom(2048)  # receive the file data
            count_total += 1
            count += 1

            if check_proceed and size > 1 and count_total == int(size / 2):
                check_proceed = False  # make sure to only get in this section once.
                ans = input("download reached 50%. To continue write 'proceed'. to stop, write anything else --> ")
                try:
                    TCP_client.send(ans.encode())
                    if ans != "proceed":
                        glo.in_download = False
                        UDP_client.close()
                        sys.exit()
                except socket.error:
                    glo.in_download = False
                    UDP_client.close()
                    sys.exit()

            data_string = data.decode()
            index = data_string.index(':')  # before the ':' is the sequence number and after is the file data
            packet_number = int(data_string[:index])
            data_list[packet_number] = data_string[index + 1:]
            packet_check_list[packet_number] = True
        except TimeoutError:
            if count == 0:
                timer += 100
                UDP_client.settimeout(timer)
                count = 0
                temp = ""
                for i in range(size):
                    if not packet_check_list[i]:  # check what packets to resent
                        temp += " {}".format(i)  # the message will be in format: "1 2 3 ..." (packet number and space)
                try:
                    TCP_client.send(temp[1:])
                    continue
                except socket.error:
                    glo.in_download = False
                    UDP_client.close()
                    sys.exit()

    UDP_client.close()
    TCP_client.send("stop".encode())  # if finished, send 'stop'
    new_name = input("enter file new name ")
    glo.in_download = False
    with open(new_name, 'w') as file:
        for i in data_list:
            file.write(i)
    sys.exit()


def receive(TCP_client, glo) -> None:
    """
    infinite loop to receive messages. If the message was "disconnected" then it means we asked to be
    disconnected and the server successfully did that. if the message start with '|' it means we asked to download a
    specific file, and the server replied that the file exist and will be sent to the client (the message will
    include the amount of packets to be sent, another '|' and the new port number of the server). If the messages is
    regular message, we will display it and move on.
    :param glo: we store here global data from all threads to read.
    :param TCP_client: the client tcp socket
    :return:
    """
    while True:
        try:
            message = TCP_client.recv(4096).decode()
            if message[0] == '|':
                UDP_thread = threading.Thread(target=get_file, args=(TCP_client, int(message[1:]), glo))
                UDP_thread.start()
            else:
                print(message)
                if message == "Can't download. Need to log in first" or message == "Can't download. File not found":
                    glo.in_download = False
                elif message == "disconnected":
                    sys.exit()
        except socket.error:
            sys.exit()


def write(connection: bool, glo) -> None:
    """
    infinite loop to get the user command input and send messages to the server (we use other functions to write the
    message according to the user command input). If we are not connected to the server via tcp, we use the 'start'
    function in order to connect the client to the server. After doing that, we create new thread  for receiving
    messages.
    :param glo: we store here global data from all threads to read.
    :param connection: True or False if client connected currently to server via tcp
    :return:
    """
    while True:  # message layout
        if not connection:
            TCP_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket initialization
            start(TCP_client)
            connection = True
            new_receive_thread = threading.Thread(target=receive, args=(TCP_client, glo))
            new_receive_thread.start()
        try:
            txt: str = input()
            if txt == "connect":
                message = connect()
                TCP_client.send(message.encode())
            elif txt == "disconnect":
                TCP_client.send("{}".format(txt).encode())
                connection = False
            elif txt == "get_users":
                TCP_client.send("{}".format(txt).encode())
            elif txt == "get_list_file":
                TCP_client.send("{}".format(txt).encode())
            elif txt == "download":
                message = download()
                TCP_client.send(message.encode())
                glo.in_download = True
                while glo.in_download:
                    time.sleep(0.5)
            else:
                message = send(txt)
                TCP_client.send(message.encode())
        except socket.error:
            print("\ncant reach the server")
            connection = False


def connect() -> str:
    """
    take name input from the user and do that until the name is legal to use (does not have '<' or '>' in it)
    :return: the full message to be sent to the server
    """
    while True:
        name = input("Enter name --> ")
        if name == "":
            print("Can't use empty string as name. Try again")
            continue
        if '|' not in name:
            return "connect|{}".format(name)
        else:
            print("Can't put '|' in the name. Try again")


def send(txt: str) -> str:
    """
    take name input and msg data input from the user and create the full message to be sent to the server.
    if message is for all, do not fill the 'name' part (keep empty)
    :param txt: The message the user wanted to send
    :return: the full message to be sent to the server
    """
    print("\nenter name (keep empty if message is to all)")
    name = input()
    if name == "":
        return "msg_all|{}".format(txt)
    else:
        return "msg|{}|{}".format(name, txt)


def download() -> str:
    """
    take file name as input
    :return: the full message to be sent to the server
    """
    print("\nenter file name")
    file_name = input()
    return "download|{}".format(file_name)


if __name__ == '__main__':
    glo_object = Globals()  # we store here global data from all threads to read.
    write(False, glo_object)
