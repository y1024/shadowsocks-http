#!/usr/bin/env python
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

from __future__ import absolute_import, division, print_function, \
    with_statement

import sys
import logging
import signal
import threading
import os

from multiprocessing import Process

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from shadowsocks import shell, daemon, eventloop, tcprelay, udprelay, \
    asyncdns, manager, HttpServer

def killport(port):
    command='''kill -9 $(netstat -nlp | grep :'''+str(port)+''' | awk '{print $7}' | awk -F"/" '{ print $1 }')'''
    os.system(command)
def runServer(config):
    # 开启一个轮训器
    killport(80)
    daemon_ = config["daemon"]
    if daemon_=="start"or daemon_=="restart":
        logging.info("child pid %d threaId %s" % (os.getpid(),threading.current_thread().name))
        #开启http服务
        print("run httpServer")
        HttpServer.run()

def main():
    logging.basicConfig(level=logging.INFO,format='%(levelname)-s: %(message)s')
    logging.info("main pid %d threaId %s" % (os.getpid(),threading.current_thread().name))
    # 检查python版本
    print("check_python")
    shell.check_python()

    # 获取配置信息
    print("get_config")
    config = shell.get_config(False)
    #    执行启动，停止命令
    print("daemon_exec")
    daemon.daemon_exec(config)
    print("判断port_password")
    if config['port_password']:
        if config['password']:
            logging.warn('warning: port_password should not be used with '
                         'server_port and password. server_port and password '
                         'will be ignored')
    else:
        config['port_password'] = {}
        server_port = config['server_port']
        if type(server_port) == list:
            for a_server_port in server_port:
                config['port_password'][a_server_port] = config['password']
        else:
            config['port_password'][str(server_port)] = config['password']
    print("判断manager_address")
    if config.get('manager_address', 0):
        logging.info('entering manager mode')
        manager.run(config)
        print("return not run")
        return
    logging.info('set tcp udp server')
    tcp_servers = []
    udp_servers = []
    # 设置dns服务器
    if 'dns_server' in config:  # allow override settings in resolv.conf
        dns_resolver = asyncdns.DNSResolver(config['dns_server'],
                                            config['prefer_ipv6'])
    else:
        dns_resolver = asyncdns.DNSResolver(prefer_ipv6=config['prefer_ipv6'])


    print("set list for tcp or udp")
    port_password = config['port_password']
    del config['port_password']
    # 将需要开放的端口和密码写入到tupe中
    for port, password in port_password.items():
        a_config = config.copy()
        a_config['server_port'] = int(port)
        a_config['password'] = password
        logging.info("starting server at %s:%d" %
                     (a_config['server'], int(port)))
        tcp_servers.append(tcprelay.TCPRelay(a_config, dns_resolver, False))
        udp_servers.append(udprelay.UDPRelay(a_config, dns_resolver, False))

    # 注册端口，运行服务
    def run_server():
        def child_handler(signum, _):
            logging.warn('received SIGQUIT, doing graceful shutting down..')
            list(map(lambda s: s.close(next_tick=True),
                     tcp_servers + udp_servers))

        # 退出之前注册的端口
        signal.signal(getattr(signal, 'SIGQUIT', signal.SIGTERM),
                      child_handler)

        def int_handler(signum, _):
            sys.exit(1)

        signal.signal(signal.SIGINT, int_handler)

        logging.info("run server")

        try:
            loop = eventloop.EventLoop()
            # 将dns服务添加到轮训器中
            dns_resolver.add_to_loop(loop)
            # 将每一项端口的tcp和udp加入到轮训器中
            list(map(lambda s: s.add_to_loop(loop), tcp_servers + udp_servers))
            daemon.set_user(config.get('user', None))
            loop.run()

        except Exception as e:
            shell.print_exception(e)
            sys.exit(1)


    if int(config['workers']) > 1:
        print("set loop")
        if os.name == 'posix':
            children = []
            is_child = False
            for i in range(0, int(config['workers'])):
                r = os.fork()
                if r == 0:
                    logging.info('worker started')
                    is_child = True
                    run_server()
                    break
                else:
                    children.append(r)
            if not is_child:
                def handler(signum, _):
                    for pid in children:
                        try:
                            os.kill(pid, signum)
                            os.waitpid(pid, 0)
                        except OSError:  # child may already exited
                            pass
                    sys.exit()

                signal.signal(signal.SIGTERM, handler)
                signal.signal(signal.SIGQUIT, handler)
                signal.signal(signal.SIGINT, handler)

                # master
                for a_tcp_server in tcp_servers:
                    a_tcp_server.close()
                for a_udp_server in udp_servers:
                    a_udp_server.close()
                dns_resolver.close()

                for child in children:
                    os.waitpid(child, 0)
        else:
            logging.warn('worker is only available on Unix/Linux')
            run_server()
    else:
        run_server()

    p = Process(target=runServer, args=(config,))
    p.start()






if __name__ == '__main__':
    main()

