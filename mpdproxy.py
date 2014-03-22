#!/usr/bin/python

import socket
import socketserver
import argparse

from modules import mpdclient

config_servers = []


# Now create the server

class MPDProxyHandler(socketserver.StreamRequestHandler):
    global config_servers
    servers = config_servers

    def process_command(self, command):
        # pass the command to servers
        print("Sending command: {}\n".format(command))
        for server in self.servers:
            response = mpdclient.send_command(server, command)
        self.wfile.write(response.encode())
        
                    
    
    def handle(self):
        print("Connection from {}\n".format(self.request.getpeername()))
        versions = []
        for server in self.servers:
            versions.append(mpdclient.get_server_version(server))

        # Send the version of the last server of the list
        # TODO: may be better to send the lowest version number so that
        # the client only uses commands compatible with all servers
        versions.sort()
        version_response = "OK MPD {}\n".format(versions[0])
        self.wfile.write(version_response.encode())
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


parser = argparse.ArgumentParser()
parser.add_argument("-s", "--servers", help="server to control using addr[:port] format. Can be specified several times to control more servers", action="append")
parser.add_argument("-b", "--bind", help="Bind address using the form addr[:port]. Defaults to 0.0.0.0:6601", default="0.0.0.0:6601")

args = parser.parse_args()

for server in args.servers:
    description = server.split(':')
    host = 'localhost'
    port = 6600
    try:
        host = description[0]
        port = int(description[1])
    except:
        pass
    config_servers.append((host, port))

bind_description = args.bind.split(':')
bind_addr = '0.0.0.0'
bind_port = 6601
try:
    bind_addr = bind_description[0]
    bind_port = int(bind_description[1])
except:
    pass
                         
mpd_proxy = MPDProxyServer((bind_addr, bind_port), MPDProxyHandler)
mpd_proxy.serve_forever()
