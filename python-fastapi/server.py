#!/usr/bin/env python
import asyncio
import importlib
import logging
import os
import sys
import json
import multiprocessing

from fastapi import FastAPI, HTTPException, Request, Response

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
        self.logger = logging.getLogger()
        self.ch = logging.StreamHandler(sys.stdout)

        #
        # Logging setup.  TODO: Loglevel hard-coded for now. We could allow
        # functions/routes to override this somehow; or we could create
        # separate dev vs. prod environments.
        #
        self.logger.setLevel(loglevel)
        self.ch.setLevel(loglevel)
        self.ch.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(self.ch)

        if check_specialize_info_exists():
            self.logger.info('Found state.json')
            specialize_info = read_specialize_info()
            self.userfunc = self._load_v2(specialize_info)
            if self.user_proc is not None:
                self.user_proc.terminate()
            print(self.userfunc)
            self.user_proc = multiprocessing.Process(target=self.userfunc)
            self.user_proc.start()
            self.logger.info('Loaded user function {}'.format(specialize_info))

    async def load(self):
        self.logger.info("/specialize called")
        # load user function from codepath
        self.userfunc = import_src("/userfunc/user").main
        if self.user_proc is not None:
            self.user_proc.terminate()
        print(self.userfunc)
        self.user_proc = multiprocessing.Process(target=self.userfunc)
        self.user_proc.start()
        return ""

    async def loadv2(self, request: Request):
        specialize_info = await request.json()
        if check_specialize_info_exists():
            self.logger.warning("Found state.json, overwriting")
        self.userfunc = self._load_v2(specialize_info)

        if self.user_proc is not None:
            self.user_proc.terminate()
        print(self.userfunc)
        self.user_proc = multiprocessing.Process(target=self.userfunc)
        self.user_proc.start()

        store_specialize_info(specialize_info)
        return ""

    async def healthz(self):
        return "", Response(status_code=200)

    def _load_v2(self, specialize_info):
        filepath = specialize_info['filepath']
        handler = specialize_info['functionName']
        self.logger.info(
            'specialize called with  filepath = "{}"   handler = "{}"'.format(
                filepath, handler))
        # handler looks like `path.to.module.function`
        parts = handler.rsplit(".", 1)
        if len(handler) == 0:
            # default to main.main if entrypoint wasn't provided
            moduleName = 'main'
            funcName = 'main'
        elif len(parts) == 1:
            moduleName = 'main'
            funcName = parts[0]
        else:
            moduleName = parts[0]
            funcName = parts[1]
        self.logger.debug('moduleName = "{}"    funcName = "{}"'.format(
            moduleName, funcName))

        # check whether the destination is a directory or a file
        if os.path.isdir(filepath):
            # add package directory path into module search path
            sys.path.append(filepath)

            self.logger.debug('__package__ = "{}"'.format(__package__))
            if __package__:
                mod = importlib.import_module(moduleName, __package__)
            else:
                mod = importlib.import_module(moduleName)

        else:
            # load source from destination python file
            mod = import_src(filepath)

        # load user function from module
        return getattr(mod, funcName)

def main():
    import uvicorn

    app = FuncApp(LOG_LEVEL)

    app.add_api_route(path='/specialize', endpoint=app.load, methods=["POST"])
    app.add_api_route(path='/v2/specialize', endpoint=app.loadv2, methods=["POST"])
    app.add_api_route(path='/healthz', endpoint=app.healthz, methods=["GET"])

    uvicorn.run(app, host="0.0.0.0", port=9999, log_level=LOG_LEVEL)

main()