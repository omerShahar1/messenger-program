## How our program works:
Here are the steps to activate the program.
1.	Run Server.py 
2.	Run Client.py
3.	Client program will ask for the IP address you will connect from, the IP address of the server (write 127.0.0.1 if this is your local network) and the destination port (you can choose any port from 55000 to 55015, they are all active).
4.	Write command or messages (look down for explanation).


## What command can you write:
•	to connect, you will need to write the command: “connect”. 
The client will ask you after to write the name you chose (the name can’t have ‘|’ in it). If the name was legal then the client will send the message to the server, and you will receive back message of ‘connected’ as sign of successes. If the name you chose was taken, the server will not connect you and send back the message: “can't connect. Name is taken. Try another”. And you will need to connect again with another name.

•	To disconnect, you will need to write the command: “disconnect”.
The server will disconnect you from the tcp connection and you will be directed to step 3 from above. Notice that the command will disconnect you from the tcp connection and alse reverse the action of the connect function.
The action will try to send all users the message: “<name> is connected” and send back to your Client: “connected”.

•	to get list of online users, you will need to write the command: “get_users”.
The server will try to return that list to you. You don’t need to be connected to do that task, but you do need to have tcp connection.

•	to get list of files, you will need to write the command: “get_list_file”.
The server will try to return that list to you. You don’t need to be connected to do that task, but you do need to have tcp connection.

•	To download, you will need to write the command: “download”.
The client will ask you to provide the name of the file you want to download. Then after the download reached 20%, the Client program will ask you if you want to proceed. If you do, write down ‘proceed’ or write down anything else if you want to stop. In case you stopped, the server will send you message “download stopped”. But if you finished downloading the file, the server will send the message: ”User <your name> downloaded 100% out of file. Last byte is: <last byte> “. Then the Client program will ask you to provide the file new name. Note that you must be connected to do that action. If the file you chose does not exist in the server, you will receive the message: “Can't download. File not found”.

•	In case your input did not match any of the option above, the program will take it as a message.  The program then will ask you to provide the target name (leave blank if this is a message to all the users). In case you chose to send message to all users, the server will receive: “msg_all|<message_data>”. Otherwise the server will receive: “msg|<message_data>|<target_name>”. Note that you must be connected to do that action. 

### About the client program:
The client program starts by create tcp socket and asking you to give it an address and the address of the server for tcp connection.
Then the program will create new thread of infinite loop with the purpose of receive messages from the server and handle them (print them or act upon them). Your current thread will be also in infinite loop with the purpose of writing messages and commands to the server (look at the syntax above). The program is prepared for problem from the server side and if the tcp connection with the server stopped (for example if you close the server program before the client), the client will simply go back to step 3 in the steps above.

### About the server program:
The server starts simply by running the program. No extra action is needed. The server has dictionary where it keeps the online client sockets by using they’re names as keys). The server creates tcp socket for every port in range (55000 – 55015), bind it and create new thread that socket with the task of listen in a infinite loop and wait for incoming tcp connections. Once connection achieved, the server creates new thread to handle the new client messages and requests while the current thread continue to wait for incoming connections (max 15 connections at the same time in every port). 
The server handles each client using infinite loop to receive messages from it, and act accordingly. The server is prepared for problem from the client (client connection and socket not working for example) and in case that happened the server will close the connection with the client (disconnect it) and close the thread handling that client (allowing other clients to connect)


### How the download works:
•	The client sends to the server message: “download|<file name>”. The server in his turn, check if the client is connected and if the file exists. If both true, the server will open the file and devide its data to parts of 2043 bytes (each been saved in a list where the location in the list is the sequence number. The sequence number and the char ‘:’ will be saved there too as the first 5 bytes since, integer takes 4 bytes and char only one). The Server then close the file and send to the client via tcp the number of packets that will arrive. The client receives that message (and will know to handle it correctly because it starts with ‘|’ as the first char of the string). The client read that and create new thread to handle the download. The client will then create udp socket with time out of 100 milliseconds and a list of the given size to save the file data. The client then sends via tcp its udp socket port number (IP is the same as the tcp socket and the server already have that information). The server receives that information, create udp socket and send all the packets to the client. After finishing sending all the packets the udp server socket wait for message to arrive from the client (via udp). The client will receive the data in a loop until all packets arrived or until there was a TimeoutError. If the error happened, the socket would increase its timer by 100 milliseconds and send to the server via tcp all the packets numbers that need to be resend (and go back to wait for new packets to arrive via udp). After reaching 50% download, the server will stop and wait to hear from the client if it wants to proceed. The client will inform you (the user) about it and ask you to provide the answer. If you want to proceed you write ‘proceed’. If you write anything else, the download will stop.
After download is finished the client send ‘stop’ order via tcp to the server. the server sends the client notice and the last byte to be sent.
The client ask you to provide the file new name and the client then saves the file data in that file.

Example for running the program. As you can see, we started by writing down the client IP, and the server address (we used the same computer for running the server and the client so we just gave the local network).
Then I connected to the server by writing ‘connect’ and then I provide my client’s name (‘client1’). Then I wrote ‘hello!’ and was instructed to write the name of the user this message is for. I did not give a name and the message was sent to all the users. Then we requested the list of clients and the list of files (by writing: ‘get_users’ and ‘get_list_file’).
Then I wanted to download one of the files so I wrote ‘download’ and was instructed to write the file name (I wrote ‘q.txt’). the download process stopped at 50% and asked if I wanted to proceed. I answer by writing ‘proceed’ and then after the download was completed, I wrote the file new name.
Finaly, I disconnected by writing ‘disconnect’ and was disconnected from the server (and went back to the start of the program to create TCP socket and connect to the server). 
 
  

As can be seen in the following Wireshark testing (who were submitted with the rest of the files) we established the connection from two different IP addresses (local network and the WSL). We pointed at the UDP packet because it is the download action from the server to the client.
 







