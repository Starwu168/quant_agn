"""日志模块：创建统一格式的控制台日志器。"""

import logging


def get_logger(name: str = "stock-agent"):
    """按统一格式创建日志器，避免重复添加 handler。"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger
