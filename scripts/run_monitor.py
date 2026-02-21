"""程序入口：启动盯盘服务并持续运行。"""

import os

from modules.dingpan.monitor_loop import MonitorService

svc = MonitorService("C:/Users\wind2\PycharmProjects\quant_agn\pre\config\monitor.yaml")
svc.run_forever()
