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

# Some tool functions to connect to MPD servers
import socket


########################################################
def connect_and_apply(host, function):
    """
    Connects to a MPD server and call function with the corresponding socket.
    Returns the result of function or None if error
    """
    try:
        s = socket.create_connection(host)
    except OSError as e:
        sys.stderr.write("Failed to connect to {}: {}\n".format(host, e))
        return None
    s.settimeout(2)
    return function(s)

########################################################
def get_server_version(host):
    """
    Returns the version of an MPD server. host is an address port tuple accepted by socket.create_connection
    """
    def get_version(s):
        with s.makefile(mode='rw', buffering=1) as f:
            response = f.readline()
            version_words = response.split(' ')
            if len(version_words) < 3:
                return ''
            return version_words[2].rstrip()
    return connect_and_apply(host, get_version)


########################################################
def send_command(host, command):
    """
    Sends a command to a MPD server. host is an address port tuple accepted by socket.create_connection
    """
    if command == "idle\n":
        return ''
    if command == "noidle\n":
        return 'OK\n'
    def send_command(s):
        with s.makefile(mode='rw', buffering=1) as f:
            response = f.readline()
            # Send command
            f.write(command)
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
    return connect_and_apply(host, send_command)
