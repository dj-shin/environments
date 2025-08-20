#!/usr/bin/env python
import importlib
import os
import sys
import runpy

USERFUNCVOL = os.environ.get("USERFUNCVOL", "/userfunc")

def import_src(path):
    return importlib.machinery.SourceFileLoader("mod", path).load_module()

def load_v2(filepath, handler):
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

    # check whether the destination is a directory or a file
    if os.path.isdir(filepath):
        # add package directory path into module search path
        sys.path.append(filepath)

        if __package__:
            mod = importlib.import_module(moduleName, __package__)
        else:
            mod = importlib.import_module(moduleName)

    else:
        # load source from destination python file
        mod = import_src(filepath)

    # load user function from module
    runpy.run_path(mod.__file__, run_name="__main__")


def main():
    filepath = sys.argv[1]
    handler = sys.argv[2]
    load_v2(filepath, handler)

main()