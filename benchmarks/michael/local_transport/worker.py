"""Fixed action worker; every invocation is inside MXC, including file operations."""
import json
import os
import sys

LIMIT = 8192
request = json.loads(sys.stdin.buffer.read(LIMIT + 1))
operation, path = request["op"], request["path"]
if path not in ("candidate.py", "result.txt"):
    raise ValueError("path denied")
if operation == "run":
    if path != "candidate.py":
        raise ValueError("execution path denied")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    os.close(descriptor)
    os.execv(sys.executable, [sys.executable, "-I", "-B", path])
elif operation in ("read", "write"):
    flags = os.O_NOFOLLOW | (os.O_RDONLY if operation == "read" else
                            os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "rb" if operation == "read" else "wb") as stream:
        if operation == "write":
            data = request["data"].encode()
            if len(data) > LIMIT:
                raise ValueError("write overflow")
            stream.write(data)
            print("written")
        else:
            data = stream.read(LIMIT + 1)
            if len(data) > LIMIT:
                raise ValueError("read overflow")
            sys.stdout.buffer.write(data)
else:
    raise ValueError("operation denied")
