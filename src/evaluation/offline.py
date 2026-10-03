"""Fail closed if evaluation accidentally attempts a network connection."""
from contextlib import contextmanager
import socket
from unittest.mock import patch


@contextmanager
def network_blocked():
    def denied(*args, **kwargs):
        raise RuntimeError("Evaluation is offline: network connection blocked")
    with patch.object(socket.socket, "connect", denied), \
            patch.object(socket.socket, "connect_ex", denied), \
            patch.object(socket, "create_connection", denied):
        yield
