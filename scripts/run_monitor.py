from common.config import MonitorSettings
from monitor.monitor_loop import MonitorService

# 创建配置
settings = MonitorSettings()

# 初始化 MonitorService
svc = MonitorService(settings)

# 启动监控服务
svc.run_forever()
