"""Untrusted-side staging of a host-constructed, answer-free archive from stdin."""
import io
import runpy
import sys
import tarfile

with tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read(400000))) as archive:
    archive.extractall("/work/app", filter="data")
runpy.run_path("/work/app/harness.py", run_name="__main__")
