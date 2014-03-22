import socket


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

def get_server_version(host):
    def get_version(s):
        with s.makefile(mode='rw', buffering=1) as f:
            response = f.readline()
            return response
    return connect_and_apply(host, get_version)

def send_command(host, command):
    if command == "idle\n":
        return ''
    if command == "noidle\n":
        return 'OK\n'
    def send_command(s):
        with s.makefile(mode='rw', buffering=1) as f:
            response = f.readline()
            print(response)
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
