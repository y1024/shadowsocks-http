
import os

rootDir = os.path.abspath(".")
print(rootDir)
configPath=os.path.join(rootDir,"config")
filePath = os.path.join(configPath, "shadowsocks.json")
if os.path.exists(filePath):
    print("文件存在")
else:
    print("文件不存在")
