"""Synthetic MXC probe: never reads real credentials or asks Keychain for items."""
import ctypes
import errno
import json
import socket
import sys
from pathlib import Path

task, denied, port = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
results = {}
(task / "allowed.txt").write_text("synthetic\n")
assert (task / "allowed.txt").read_text() == "synthetic\n"
results["workspace_read_write"] = "allowed"
try:
    (denied / "credential-fixture").read_bytes()
except OSError as exc:
    assert exc.errno == errno.EPERM, repr(exc)
    results["synthetic_credential_read"] = {"denied_errno": exc.errno}
else:
    raise AssertionError("denied credential fixture readable")
try:
    (denied / "new-file").write_text("synthetic\n")
except OSError as exc:
    assert exc.errno == errno.EPERM, repr(exc)
    results["outside_write"] = {"denied_errno": exc.errno}
else:
    raise AssertionError("denied write allowed")
for name, address in (
    ("outbound", ("192.0.2.1", 443)), ("owned_loopback", ("127.0.0.1", port)),
):
    with socket.socket() as connection:
        connection.settimeout(1)
        try:
            connection.connect(address)
        except OSError as exc:
            assert exc.errno == errno.EPERM, repr(exc)
            results[name] = {"denied_errno": exc.errno}
        else:
            raise AssertionError("task network allowed")
system = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
bootstrap = ctypes.c_uint.in_dll(system, "bootstrap_port")
service = ctypes.c_uint()
lookup = system.bootstrap_look_up
lookup.argtypes = [ctypes.c_uint, ctypes.c_char_p, ctypes.POINTER(ctypes.c_uint)]
lookup.restype = ctypes.c_int
status = lookup(bootstrap, b"com.apple.securityd", ctypes.byref(service))
assert status == 1100, f"securityd lookup was not denied: {status}"
results["keychain_service_lookup"] = {"bootstrap_status": status, "items_queried": 0}
print(json.dumps(results, sort_keys=True))
