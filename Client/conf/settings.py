# -*- coding:utf-8 -*-

import os

#远端接受数据的服务器
Params = {
	"server": "192.168.2.108",
	"port": 8000,
	'url': '/assets/report/',
	'request_timeout': 30,
}

#日志文件配置
PATH = os.path.join(os.path.dirname(os.getcwd()),'log','cmdb.log')

#更多的配置，都集中此文件中