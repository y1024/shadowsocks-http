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


import json
import sys,os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))



def getConfigByFile():
    config={}
    rootDir = os.path.abspath(".")
    print(rootDir)
    configPath=os.path.join(rootDir,"config")
    config["pid-file"]=os.path.join(configPath,'shadowsocks.pid')
    config["log-file"]=os.path.join(configPath,'shadowsocks.log')
    filePath = os.path.join(configPath, "shadowsocks.json")
    if os.path.exists(filePath):
        with open(filePath, 'rb') as f:
            try:

                newConfig=json.loads(f.read().decode('utf8'))
                for d,x in newConfig.items():
                    config[d]=x
                return config
            except ValueError as e:
                sys.exit(1)
    else:
        return config;




def getArgs(argv):
    config = getConfigByFile()
    argv.pop(0)
    argv_ = int(len(argv) / 2)
    for x in range(argv_):
        # 获取索引
        keyIndex = 2 * x
        valueIndex = keyIndex + 1;

        key = argv[keyIndex]
        vaule = argv[valueIndex]
        newKey = key.replace("-", "")
        if newKey == 'd':
            config["daemon"]=vaule
    return config
    pass


def getConfig():
    argv = sys.argv
    if len(argv) > 1 and len(argv) % 2 == 1:
         config = getArgs(argv)
         if len(config)==0:
             onError()
         else:return config
    else:
        onError()


def onError():
    print("please right to command")
    sys.exit(1)


# print(getConfig())
