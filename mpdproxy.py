#!/usr/bin/python

import socket
import sys
import select
import socketserver

config_servers = [
    {
        "host": "127.0.0.1",
        "port": 6600
    },
    {
        "host": "music",
        "port": 6600
    },
    ]


local_port = 6601


# Now create the server

class MPDProxyHandler(socketserver.StreamRequestHandler):

    servers = config_servers

    def get_server_version(self, host, port):
        try:
            s = socket.create_connection((host, port))
        except OSError as e:
            sys.stderr.write("Failed to connect to {}:{}: {}\n".format(server["host"], server["port"], e))
            return 'ACK\n'
        s.settimeout(2)
        with s.makefile(mode='rw', buffering=1) as f:
            response = f.readline()
            return response

    def send_command_to_server(self, cmd, host, port):
        """Sends a command to a mpd server and return its response.  This command
        is blocking (connects to the server, send command, gets response
        and close connection)
        """
        if cmd == "idle\n":
            return ''
        if cmd == "noidle\n":
            return 'OK\n'
        try:
            s = socket.create_connection((host, port))
        except OSError as e:
            sys.stderr.write("Failed to connect to {}:{}: {}\n".format(server["host"], server["port"], e))
            return 'KO\n'
        s.settimeout(2)
        with s.makefile(mode='rw', buffering=1) as f:
            response = f.readline()
            print(response)
            # Send command
            f.write(cmd)
            # Get answer
            response = ''
            while True:
                line = f.readline()
                response = response + line
                if not line or line.startswith("OK") or line.startswith("ACK"):
                    break
        s.shutdown(socket.SHUT_RDWR)
        s.close()
        return response

    def process_command(self, command):
        # pass the command to servers
        print("Sending command: {}\n".format(command))
        for server in self.servers:
            response = self.send_command_to_server(command, server['host'], server['port'])
        self.wfile.write(response.encode())
        
                    
    
    def handle(self):
        print("Connection from {}\n".format(self.request.getpeername()))
        for server in self.servers:
            version = self.get_server_version(server['host'], server['port'])
        self.wfile.write(version.encode())
        command_list_started = False
        cmd = ''
        while True:
            line = self.rfile.readline().decode()
            if not line:
                return
            if line == 'command_list_begin\n' or line == 'command_list_ok_begin\n':
                # Multiple line command
                cmd = cmd + line
                command_list_started = True
            elif line == 'command_list_end\n':
                cmd = cmd + line
                command_list_started = False
            else:
                cmd = cmd + line
            if not command_list_started:
                # Command is complete
                self.process_command(cmd)
                cmd = ''

class MPDProxyServer(socketserver.TCPServer):
    allow_reuse_address = True

                                
server = MPDProxyServer(('0.0.0.0', local_port), MPDProxyHandler)
server.serve_forever()
