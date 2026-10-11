import socket

def test_network_is_blocked():
    sock = socket.socket()
    try:
        sock.settimeout(2)
        try:
            sock.connect(("1.1.1.1", 80))
        except (OSError, TimeoutError):
            return
        raise AssertionError("Network connection unexpectedly succeeded")
    finally:
        sock.close()
