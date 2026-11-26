"""Disposable compose-like supervisor (stdlib only, no sockets or subprocesses).

Containers are modeled as a writable layer directory. A mount maps a container
path to a host directory: "./rel:/path" binds a directory next to compose.json,
"name:/path" uses the named volume `name`, which must be declared under the
top-level "volumes" key and persists under state/volumes/<name>. Any container
path not covered by a mount lives in the container layer, which is discarded
whenever the container is recreated.

Operations:
- up:       create missing containers and start them.
- deploy:   roll out new code with the configured deploy.strategy:
            "force-recreate" recreates every container; "restart" restarts
            existing containers in place (their layer is kept).
- recreate: recreate containers unconditionally (what an image update,
            host migration or `down`/`up` does).
"""

import importlib.util
import json
import os
from pathlib import Path
import shutil


class StackError(RuntimeError):
    pass


class Stack:
    def __init__(self, compose_path, state_dir):
        self.root = Path(compose_path).resolve().parent
        self.config = json.loads(Path(compose_path).read_text())
        self.state = Path(state_dir)
        self.running = {}
        self.generation = {}

    def _mounts(self, name):
        service = self.config["services"][name]
        declared = self.config.get("volumes") or {}
        mounts = {}
        for spec in service.get("volumes", []):
            source, target = spec.split(":", 1)
            target = "/" + target.strip("/")
            if target in mounts:
                raise StackError(f"{name}: duplicate mount target {target}")
            if source.startswith("./"):
                mounts[target] = ("bind", self.root / source[2:])
            else:
                if source not in declared:
                    raise StackError(f"{name}: volume {source!r} is not declared at top level")
                mounts[target] = ("named", self.state / "volumes" / source)
        return mounts

    def resolve(self, name, container_path):
        """Map a container path to (kind, host path) through mounts, longest prefix first."""
        container_path = "/" + container_path.strip("/")
        for target, (kind, host) in sorted(self._mounts(name).items(), key=lambda i: -len(i[0])):
            if container_path == target or container_path.startswith(target + "/"):
                return kind, host / container_path[len(target):].lstrip("/")
        layer = self.state / "layers" / f"{name}-{self.generation.get(name, 0)}"
        return "layer", layer / container_path.lstrip("/")

    def _create(self, name):
        layer = self.state / "layers" / f"{name}-{self.generation.get(name, 0)}"
        if layer.exists():
            shutil.rmtree(layer)
        self.generation[name] = self.generation.get(name, 0) + 1
        (self.state / "layers" / f"{name}-{self.generation[name]}").mkdir(parents=True)

    def _start(self, name):
        service = self.config["services"][name]
        kind, entry = self.resolve(name, service["entrypoint"])
        if not entry.is_file():
            raise StackError(f"{name}: entrypoint {service['entrypoint']} not found ({kind})")
        environment = {}
        for key, value in service.get("environment", {}).items():
            environment[key] = str(self.resolve(name, value)[1]) if str(value).startswith("/") else value
        spec = importlib.util.spec_from_file_location(f"svc_{name}", entry)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.running[name] = (module, environment)
        status, _ = self.request(name, "GET", "/healthz")
        if status != 200:
            raise StackError(f"{name}: health check failed with {status}")

    def up(self):
        for name in self.config["services"]:
            if name not in self.generation:
                self._create(name)
            if name not in self.running:
                self._start(name)

    def deploy(self):
        strategy = (self.config.get("deploy") or {}).get("strategy", "force-recreate")
        if strategy not in ("force-recreate", "restart"):
            raise StackError(f"unknown deploy strategy {strategy!r}")
        for name in self.config["services"]:
            self.running.pop(name, None)
            if strategy == "force-recreate" or name not in self.generation:
                self._create(name)
            self._start(name)

    def recreate(self):
        for name in self.config["services"]:
            self.running.pop(name, None)
            self._create(name)
            self._start(name)

    def request(self, name, method, path, body=None):
        module, environment = self.running[name]
        saved = dict(os.environ)
        os.environ.update(environment)
        try:
            return module.app(method, path, body)
        finally:
            os.environ.clear()
            os.environ.update(saved)
