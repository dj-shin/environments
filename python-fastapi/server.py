#!/usr/bin/env python
import importlib
import logging
import os
import subprocess
import sys
import json

from fastapi import FastAPI, Request, Response

try:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_LEVEL = getattr(logging, LOG_LEVEL)
except:
    LOG_LEVEL = logging.INFO

USERFUNCVOL = os.environ.get("USERFUNCVOL", "/userfunc")
RUNTIME_PORT = int(os.environ.get("RUNTIME_PORT", "8888"))

def store_specialize_info(state):
    json.dump(state, open(os.path.join(USERFUNCVOL, "state.json"), "w"))

def check_specialize_info_exists():
    return os.path.exists(os.path.join(USERFUNCVOL, "state.json"))

def read_specialize_info():
    return json.load(open(os.path.join(USERFUNCVOL, "state.json")))

def import_src(path):
    return importlib.machinery.SourceFileLoader("mod", path).load_module()

class FuncApp(FastAPI):
    def __init__(self, loglevel=logging.DEBUG):
        super(FuncApp, self).__init__()

        # init the class members
        self.userfunc = None
        self.user_proc = None

        if check_specialize_info_exists():
            specialize_info = read_specialize_info()
            self._run_process(specialize_info)

    async def load(self):
        # load user function from codepath
        self._run_process({"filepath": "/userfunc/user", "functionName": "main"})
        return ""

    def _run_process(self, specialize_info):
        self.user_proc = subprocess.Popen(
            [sys.executable, "-u", "launcher.py", specialize_info['filepath'], specialize_info['functionName']],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    async def loadv2(self, request: Request):
        specialize_info = await request.json()
        if self.user_proc is not None:
            self.user_proc.terminate()
        self._run_process(specialize_info)
        store_specialize_info(specialize_info)
        return ""

    async def healthz(self):
        return "", Response(status_code=200)

def main():
    import uvicorn

    app = FuncApp(LOG_LEVEL)

    app.add_api_route(path='/specialize', endpoint=app.load, methods=["POST"])
    app.add_api_route(path='/v2/specialize', endpoint=app.loadv2, methods=["POST"])
    app.add_api_route(path='/healthz', endpoint=app.healthz, methods=["GET"])

    uvicorn.run(app, host="0.0.0.0", port=9999, log_config=None)

main()