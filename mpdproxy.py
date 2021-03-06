#!/usr/bin/python

# MPDProxy: Acts as a proxy to send MPD commands from a client to
#     multiple MPD servers Copyright (C) 2014 Michaël Hauspie
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.



import socket
import socketserver
import argparse

from modules import mpdclient

config_servers = []

########################################################
class MPDProxyHandler(socketserver.StreamRequestHandler):
    global config_servers
    servers = config_servers
    # Will be used to rewrite file Ids
    # Maps a file name to an ID
    file_id_map = {}
    

    ########################################################
    def generate_file_id(self, f):
        # TODO: will probably need to make a better SONGID generation function :)
        return len(self.file_id_map) + 1

    ########################################################
    def rewrite_response(self, server, response):
        """
        Parse the response field and modify the Id field if any.
        As servers, even when using the same database do not necessarily
        map the same Id to the same file, we will replace the Id for each server
        by an Id depending on the name.
        Meanwhile, for each server, we store a translation between our generated Id and the servers Id.
        """
        processing_file = None
        new_response = ''
        for line in response.splitlines():
            key,sep,value = line.partition(':')
            if key == 'file':
                processing_file =  value
            if key == 'Id':
                id = value
                # First seen file, generate a new Id and store it in the proxy file->id mapping
                if processing_file not in self.file_id_map:
                    self.file_id_map[processing_file] = self.generate_file_id(processing_file)
                # Rewrite response with this Id
                new_response = new_response + "Id: {}\n".format(self.file_id_map[processing_file])
                # Remember the original Id for this server
                server['file_ids'][processing_file] = id
            else:
                new_response = new_response + line + '\n'
        return new_response

    ########################################################
    def id_to_file(self, id):
        for file,fid in self.file_id_map.items():
            if id == fid:
                return file
        return None


    ########################################################
    def translate_id(self, server, id):
        """
        Translates an id from generated 'virtual' id to corresponding server id.
        The id is the one extracted from the command that we need to send to servers
        so the id must be translated according to each server
        """
        id = int(id.strip('"').rstrip('"'))
        file = self.id_to_file(id)
        if file in server['file_ids']:
            newid = server['file_ids'][file]
            return newid
        return None
            

    ########################################################
    def rewrite_command(self, server, command):
        new_command = ''
        for line in command.splitlines():
            cmd_args = line.split(' ')
            try: # If the command does not have what is expected here, just ignore the rewriting and use it raw
                if cmd_args[0] == 'playid': # playid SONGID
                    tid = self.translate_id(server, cmd_args[1])
                    if tid:
                        new_command = new_command + "playid {}\n".format(tid)
                        continue
                if cmd_args[0] == 'seekid': # seekid SONGID TIME
                    tid = self.translate_id(server, cmd_args[1])
                    if tid:
                        new_command = new_command + "seekid {} {}\n".format(tid, cmd_args[2])
                        continue
                if cmd_args[0] == 'deleteid': # deleteid SONGID
                    tid = self.translate_id(server, cmd_args[1])
                    if tid:
                        new_command = new_command + "deleteid {}\n".format(tid, cmd_args[2])
                        continue
                if cmd_args[0] == 'playlistid': # playlistid SONGID (optional SONGID)
                    if len(cmd_args) >= 1:
                        tid = self.translate_id(server, cmd_args[1])
                        if tid:
                            new_command = new_command + "playlistid {}\n".format(tid)
                            continue
                if cmd_args[0] == 'playlistmove': # playlistmove {NAME} {SONGID} {SONGPOS}
                    tid = self.translate_id(server, cmd_args[2])
                    if tid:
                        new_command = new_command + "playlistmove {} {} {}\n".format(cmd_args[1], tid, cmd_args[3])
                        continue
                # addtagid and cleartagid are not implemented on purpose
            except:
                pass
            if cmd_args[0] == 'clear': # clear map
                self.file_id_map = {}
                server['file_ids'] = {}
            new_command = new_command + line + "\n"
        return new_command

    ########################################################
    def process_command(self, command):
        # pass the command to servers
        for server in self.servers:
            cmd = self.rewrite_command(server, command)
            response = mpdclient.send_command(server['addr'], cmd)
            response = self.rewrite_response(server, response)
        self.wfile.write(response.encode())
        
                    
    
    ########################################################
    def handle(self):
        versions = []
        for server in self.servers:
            versions.append(mpdclient.get_server_version(server['addr']))

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

########################################################
class MPDProxyServer(socketserver.TCPServer):
    allow_reuse_address = True


########################################################
# Command line options
print("""
mpdproxy  Copyright (C) 2014  Michaël Hauspie
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions.
""")
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
    config_servers.append({"addr": (host, port), "file_ids": {}})

bind_description = args.bind.split(':')
bind_addr = '0.0.0.0'
bind_port = 6601
try:
    bind_addr = bind_description[0]
    bind_port = int(bind_description[1])
except:
    pass
                         
mpd_proxy = MPDProxyServer((bind_addr, bind_port), MPDProxyHandler)
try:
    mpd_proxy.serve_forever()
except KeyboardInterrupt:
    pass
