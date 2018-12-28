
主要通过http请求动态增删端口，项目仅仅在ss代码基础上增加了个aiohttp


环境： python 3
          需要安装aiohttp 库



1：配置
 
    /shadowsocks/config/shadowsocks.json
       
       max_port  :最大开通端口数量
       http_key  :http请求连接的秘钥


2：开启服务

    python managerserver.py -d start
        关闭没写好，可以用 
          ps aux|grep managerserver
          kill -9  （pid） 来关闭
   
 
  
3.http请求

  
    通用参数：每次请求都要加载里面，下面表格中就不写了
            key: 配置在/shadowsocks/config/shadowsocks.json中的http_key的值。如果key不对，下面返回结果中的code都是为-1
  
    返回结果： json字符串
      
          {
            code:状态,0正常
            msg: 
            success :是否成功
            data: 数据
          }
    
  
|描述|接口地址|请求方式        |参数   | 返回结果    |  
| --------| -------- | --------   |------- | ----- |
|index|ip|GET| |msg：为代理服务器当前时间  data:为该服务器配置的最大开通端口的数量|
|注册端口|ip/register|POST|port:端口号 password:该端口的密码 |msg：提示  data:当前开通端口的数量|
|取消注册端口|ip/unregister|POST|port:端口号 password:该端口的密码 |msg：提示  data:当前开通端口的数量|
|获取已经存在的端口|ip/getExitPort|GET|  |msg：为代理服务器当前时间  data:代理服务器已经存在的端口集合|


请求示例：

    





4：类说明，
   
   HttpServer:主要注册接口。端口啊，自己增加接口可以在这里修改
   managerserver：启动代理模块（启动代理模块的时候，可以配置请求方法之类的），和http模块
   customshell: 就一个读取配置的，要想增加启动参数在这里面配置

