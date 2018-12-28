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

from multiprocessing import Queue

import asyncio
import time
from aiohttp import web
import json


def getKey(query):
    if "key" in query:
        return query["key"]
    else:
        return "NotExits"
    pass


async def index(request):
    query = request.query
    global httpKey
    response = '';
    if getKey(query) != httpKey:
        response = createResponse(-1, '秘钥错误', False)
    else:
        global maxPort
        response = createResponse(0, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), True, str(maxPort))
    return web.Response(body=response.encode('utf-8'))
    pass



async def getExitPort(request):
    query = request.query
    global httpKey
    response = '';
    if getKey(query) != httpKey:
        response = createResponse(-1, '秘钥错误', False)
    else:
        global maxPort
        response = createResponse(0, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), True, port_list)
    return web.Response(body=response.encode('utf-8'))
    pass



def createResponse(code=0, msg='', success=True, data=''):
    response = {};
    response['code'] = code
    response['msg'] = msg
    response['success'] = success
    response['data'] = data

    s = json.dumps(response)
    return s;


port_list = [];


async def register(request):
    # 获取传递过来的参数
    query = request.query

    port = query['port']
    password = query['password']
    global httpKey
    response = '';
    if getKey(query) != httpKey:
        response = createResponse(-1, '秘钥错误', False)
    else:

        global maxPort
        if len(port_list) > maxPort:
            response = createResponse(code=-3, msg="端口数量超出限制", success=False, data=str(len(port_list)))

        else:
            # 端口存在的情况先移除
            if port in port_list:
                port_list.remove(port)
                sendMsg('unregister', password, port)
                pass

            port_list.append(port)
            response = createResponse(msg='添加端口成功', data=str(len(port_list)))
            await sendMsg('register', password, port)
    return web.Response(body=response.encode('utf-8'))
    pass


# 发送进程间的消息，通知socket5进程添加或者移除端口
async def sendMsg(action, password, port):
    data = {}
    data["action"] = action
    data["data"] = {'port': port, "password": password}
    s = json.dumps(data)
    global queue
    if not queue == None:
        queue.put(s)


async def unRegister(request):
    query = request.query
    port = query['port']
    password = query['password']
    body = ''
    global httpKey
    global port_list
    if getKey(query) != httpKey:
        body = createResponse(-1, '秘钥错误', False)
    else:
        if port in port_list:
            await sendMsg('unregister', password, port)
            port_list.remove(port)
            body = createResponse(msg="端口移除成功", data=str(len(port_list)))
        else:
            body = createResponse(code=-2, msg="端口不存在", success=False, data=str(len(port_list)))

    return web.Response(body=body.encode('utf-8'))

    pass




async def createApi(eventLoop):
    app = web.Application(loop=eventLoop)
    app.router.add_route('GET', '/', index)
    app.router.add_route('POST', '/register', register)
    app.router.add_route('POST', '/unregister', unRegister)
    app.router.add_route('GET', '/getExitPort', getExitPort)
    srv = await eventLoop.create_server(app.make_handler(), '0.0.0.0', 80)
    return srv


queue = None
httpKey = ""
maxPort = 100


def run(q, k):
    global queue
    queue = q
    global httpKey
    httpKey = k["http_key"]
    global maxPort
    maxPort = k['max_port']
    loop = asyncio.get_event_loop()
    loop.run_until_complete(createApi(loop))
    loop.run_forever()
    pass


if __name__ == '__main__':
    queue = Queue()
    config = {}
    config['http_key'] = '123456gjhgjh,.'
    config['max_port'] = 200
    run(queue, config)
