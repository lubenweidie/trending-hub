"""发布器注册中心 — 新增平台只需在这里注册一行"""
from .base import BasePublisher
from .baijiahao import BaijiahaoPublisher
from .toutiao import ToutiaoPublisher

REGISTRY = {
    "baijiahao": BaijiahaoPublisher,
    "toutiao": ToutiaoPublisher,
}
