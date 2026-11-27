FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b
RUN pip install --no-cache-dir PyYAML==6.0.2
COPY --from=node:24-slim@sha256:873f586f3794f52281bd039bf02c048a0be08fde619338f9941bad1eb6b34530 /usr/local/bin/node /usr/local/bin/node
RUN node --version
COPY . /tests/
RUN chmod -R go-rwx /tests/private && chmod 755 /tests /tests/sandbox && chmod -R a+rX /tests/sandbox
WORKDIR /tests
