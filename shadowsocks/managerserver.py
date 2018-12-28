#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2015 clowwindy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import threading
import os, sys, json
from multiprocessing import Process, Queue

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from shadowsocks.manager import Manager
from shadowsocks import HttpServer, customshell, CustomDaemon


def killport(port):
    command = '''kill -9 $(netstat -nlp | grep :''' + str(port) + ''' | awk '{print $7}' | awk -F"/" '{ print $1 }')'''
    os.system(command)


def runServer(queue, keyConfig):
    # 开启一个轮训器
    killport(80)
    logging.info("child pid %d threaId %s" % (os.getpid(), threading.current_thread().name))
    # 开启http服务
    print("run httpServer")
    HttpServer.run(queue, keyConfig)


def getMsgByThread(queue, manager, config):
    while True:
        value = queue.get(True)
        if value != None:
            body = json.loads(value)
            if body != None and body['action'] != None:
                action_ = body['action']
                if action_ == 'register':
                    a_config = config.copy()
                    a_config['server_port'] = int(body["data"]["port"])
                    a_config['password'] = body["data"]["password"]
                    manager.add_port(a_config)

                    print('add Port %d width %s' % (a_config['server_port'], a_config['password']))
                elif action_ == "unregister":
                    a_config = config.copy()
                    # 解除注册
                    a_config['server_port'] = int(body["data"]["port"])
                    a_config['password'] = body["data"]["password"]
                    manager.remove_port(a_config)
            pass
    pass


def runSocket(queue):
    config = {
        'server': '0.0.0.0',
        'local_address': '127.0.0.1',
        'local_port': 1080,
        'port_password': {
        },
        'method': 'aes-256-cfb',
        'manager_address': '127.0.0.1:6001',
        'timeout': 60,
        'fast_open': False,
        'verbose': 2
    }
    manager = Manager(config)
    ##在子线程中接收消息
    t = threading.Thread(target=getMsgByThread, name='queueThread', args=(queue, manager, config))
    t.start()
    manager.run()
    pass


def work():
    config = customshell.getConfig()
    CustomDaemon.daemon_exec(config)
    queue = Queue()
    # 开启http服务
    p = Process(target=runSocket, args=(queue,))
    p.start()
    # 开启socket5服务
    p2 = Process(target=runServer, args=(queue, config,))
    p2.start()


if __name__ == '__main__':
    work()
