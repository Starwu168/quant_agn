import socket
from dataclasses import dataclass
from typing import Optional, Tuple

from pytdx.hq import TdxHq_API
from pytdx.util.best_ip import select_best_ip  # 自动选最快IP


@dataclass
class TdxConn:
    ip: str
    port: int


class PyTdxClient:
    """
    - 自动选最优通达信行情服务器
    - 维持连接（断了就重连）
    """
    def __init__(self, timeout: int = 10):
        socket.setdefaulttimeout(timeout)
        self.api = TdxHq_API(auto_retry=True, raise_exception=False)
        self.conn: Optional[TdxConn] = None

    def connect_best(self) -> TdxConn:
        info = select_best_ip()  # {'ip':..., 'port':...}
        ip, port = info["ip"], info["port"]
        ok = self.api.connect(ip, port)
        if not ok:
            raise RuntimeError(f"pytdx connect failed: {ip}:{port}")
        self.conn = TdxConn(ip=ip, port=port)
        return self.conn

    def ensure_connected(self):
        if self.conn is None:
            self.connect_best()
            return
        # 简单心跳：尝试取深圳市场证券数量
        try:
            _ = self.api.get_security_count(0)
        except Exception:
            # 断线重连
            try:
                self.api.disconnect()
            except Exception:
                pass
            self.connect_best()

    def disconnect(self):
        try:
            self.api.disconnect()
        except Exception:
            pass
