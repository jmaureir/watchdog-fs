#!/usr/bin/env python3
import os
import sys
import time
import logging
import importlib
from inspect import getmembers, isfunction
from glob import glob
from watchdog.observers import Observer
from watchdog.events import FileSystemEvent, FileClosedEvent,LoggingEventHandler,FileSystemEventHandler
import configparser
import argparse

# Promise
from threading import Event, Thread, Lock
from queue import Queue

class Promise(Thread):
    def __init__(self, function, *args, **kw_args):
        super().__init__(*args, **kw_args)
        self.function = function
        self.resolved = False
        self.rejected = False
        self.value    = None

        self.evt      = Event()
        self.lock     = Lock()

    def run(self):
        # fulfill the promese
        args    = self.fn_args
        kw_args = self.fn_kw_args
        with self.lock:
            try:
                result = self.function(*args,**kw_args)
                self.resolve(result)
            except Exception as e:
                self.reject(e)
    
    def __call__(self,*args,**kw_args):
        self.fn_args = args
        self.fn_kw_args = kw_args
        self.start()
    
    def resolve(self, value):
        self.resolved = True
        self.value    = value
        self.evt.set()
    
    def reject(self, value):
        self.rejected = True
        self.value    = value
        self.evt.set()
    
    def get(self):
        with self.lock:
            if not self.isFulfilled():
                self.evt.wait()
    
            self.join()
            
        if self.resolved:
            return self.value
        elif self.rejected:
            raise self.value

    def isFulfilled(self):
        return self.evt.is_set()
    
    def __repr__(self):
        if not self.isFulfilled():
            return "<Promise[pending]>"
        else:
            if self.resolved:
                return "<Promise[resolved with value %s]>" % self.value
            if self.rejected:
                return "<Promise[rejected with value %s]>" % self.value

class ActionHandler(object):
    def __init__(self, key, fn_handler, **kw_args):
        self.fn_handler = fn_handler
        self.key        = key

    def actionPerformed(self, key, *args, **kw_args):
        if key == self.key:
            print("triggering action %s: %s %s %s" % (key, self.fn_handler, args, kw_args))
            ret = self.fn_handler(*args, **kw_args)
            return ret

class DelayedActionHandler(object):
    def __init__(self, key, fn_handler, delay=0, **kw_args):
        self.fn_handler = fn_handler
        self.key        = key
        self.delay      = delay

        self.promises   = []

    def actionPerformed(self, key, *args, **kw_args):
        if key == self.key:
            def action(*a_args, **a_kw_args):
                try:
                    print("scheduling delayed action %s: %s %s" % (key, self.fn_handler, kw_args))
                    time.sleep(self.delay)
                    print("triggering delayed action %s: %s %s %s" % (key, self.fn_handler, a_args, a_kw_args))
                    ret = self.fn_handler(*a_args, **a_kw_args)
                    return ret
                except Exception as e:
                    print("Error performing action %s %s (args:%s kw_args:%s)" % (key,e,a_args, a_kw_args))
                    raise e

            p = Promise(action)
            self.promises.append(p(*args, key=key, **kw_args))

            if p.isFulfilled():
                print(p)

class FileEventHandler(FileSystemEventHandler):
    def __init__(self, **kw_args):
        super().__init__(**kw_args)
        self.action_handlers = []

    def addActionHandler(self, ah):
        self.action_handlers.append(ah)

    def on_any_event(self, event: FileClosedEvent) -> None:
        for ah in self.action_handlers:
            ah.actionPerformed(type(event).__name__, event=event )

class LoogedFileEventHandler(FileEventHandler):
    def __init__(self, **kw_args) -> None:
        super().__init__(**kw_args)
        self.logger = logging.getLogger("LoogedFileEventHandler")

    def on_any_event(self, event: FileClosedEvent) -> None:
        super().on_any_event(event)
        self.logger.info(str(event))

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

# parse command line args
parser = argparse.ArgumentParser()
parser.add_argument("-c",default="etc/watchdog-fs.ini")
parser.add_argument("-a",default="actions.d")

args = parser.parse_args()

# load the config file
cfg_file = args.c
print("using config file %s" % cfg_file)
config = configparser.ConfigParser()
config.read(cfg_file)

# load action scripts

action_path = args.a
action_fn_dict = {}

for action_script in glob("%s/*" % action_path):
    if os.path.isfile(action_script):
        spec = importlib.util.spec_from_file_location("*",action_script)
        module = importlib.util.module_from_spec(spec)    
        spec.loader.exec_module(module)
        fn_lst=getmembers(module,isfunction)
        for fn_name, fn in fn_lst:
            action_fn_dict[fn_name] = fn

print("%d action functions loaded" % len(action_fn_dict))

if len(action_fn_dict) == 0:
    raise RuntimeError("No action functions defined")

observer = Observer()

for section in config.sections():
    evh = config[section]

    path           = None
    event_name     = None
    action_hanlder = None

    if evh.get("path",None) is not None:
        path=evh["path"]
    if evh.get("event",None) is not None:
        event_name = evh["event"]
    if evh["type"] == "ActionHandler":
        action_handler = ActionHandler
    elif evh["type"] == "DelayedActionHandler":
        action_handler = DelayedActionHandler
    else:
        raise RuntimeError("unknown action handler")

    if path is None:
        raise RuntimeError("each event must have a path defined")

    if event_name is None:
        raise RuntimeError("event must be one supported by watchdog. see python watchdog doc")

    action_fn_name = evh.get("action",None)
    delay = evh.get("delay",0)
   
    if action_fn_name in action_fn_dict:
        fn = action_fn_dict[action_fn_name]
        event_handler = LoogedFileEventHandler()
        event_handler.addActionHandler(action_handler(event_name,fn, delay=int(delay)))
        observer.schedule(event_handler, path, recursive=True)
   
    else:
        raise RuntimeError("function %s not found in action function dictionary" % action_fn_name)

observer.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
