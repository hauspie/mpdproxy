#!/usr/bin/python

import socket
import sys
import select
import socketserver

from modules import mpdclient

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

    def process_command(self, command):
        # pass the command to servers
        print("Sending command: {}\n".format(command))
        for server in self.servers:
            response = mpdclient.send_command((server['host'], server['port']), command)
        self.wfile.write(response.encode())
        
                    
    
    def handle(self):
        print("Connection from {}\n".format(self.request.getpeername()))
        for server in self.servers:
            version = mpdclient.get_server_version((server['host'], server['port']))

        # Send the version of the last server of the list
        # TODO: may be better to send the lowest version number so that
        # the client only uses commands compatible with all servers
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
