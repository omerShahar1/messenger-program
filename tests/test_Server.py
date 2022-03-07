import os
import socket
import threading
from unittest import TestCase
import Server
import Client


class Test(TestCase):
    def test_send(self):
        online_users = {}  # key is the name. value is the client socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket initialization
        tcp_socket.bind(("", 55000))
        tcp_socket.listen(15)
        port_thread = threading.Thread(target=Server.receive, args=(tcp_socket, online_users, 55000))
        port_thread.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.bind(("", 0))
        client.connect(('127.0.0.1', 55000))
        client.send("msg_all_hello|client1".encode())
        message = client.recv(1024).decode()
        self.assertEqual(message, "Can't send message. Need to log in first")

    def test_disconnect(self):
        online_users = {}  # key is the name. value is the client socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket initialization
        tcp_socket.bind(("", 55000))
        tcp_socket.listen(15)
        port_thread = threading.Thread(target=Server.receive, args=(tcp_socket, online_users, 55000))
        port_thread.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.bind(("", 0))
        client.connect(('127.0.0.1', 55000))
        client.send("disconnect".encode())
        message = client.recv(1024).decode()
        self.assertEqual(message, "disconnected")

    def test_get_users(self):
        online_users = {}  # key is the name. value is the client socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket initialization
        tcp_socket.bind(("", 55000))
        tcp_socket.listen(15)
        port_thread = threading.Thread(target=Server.receive, args=(tcp_socket, online_users, 55000))
        port_thread.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.bind(("", 0))
        client.connect(('127.0.0.1', 55000))
        client.send("get_users".encode())
        message = client.recv(1024).decode()
        self.assertEqual(message, "users: []")

    def test_connect(self):
        online_users = {}  # key is the name. value is the client socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP socket initialization
        tcp_socket.bind(("", 55000))
        tcp_socket.listen(15)
        port_thread = threading.Thread(target=Server.receive, args=(tcp_socket, online_users, 55000))
        port_thread.start()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.bind(("", 0))
        client.connect(('127.0.0.1', 55000))
        client.send("connect|client1".encode())
        message = client.recv(1024).decode()
        self.assertEqual(message, "client1 is connected")
        message = client.recv(1024).decode()
        self.assertEqual(message, "connected")
