#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
企业级异步HTTP客户端
"""

from .client import (
    # 主要类
    AsyncHttpClient,
    
    # 配置类
    RetryConfig,
    TimeoutConfig,
    PoolConfig,
    RequestMetrics,
    
    # 拦截器
    RequestInterceptor,
    LoggingInterceptor,
    MetricsInterceptor,
    
    # 限流器
    RateLimiter,
    
    # 工厂函数
    create_http_client,
    
    # 全局函数
    get,
    post,
    put,
    delete,
    get_global_client,
    close_global_client,
)

__version__ = "1.0.0"
__author__ = "Mr.Hat"
__email__ = "contact@example.com"

__all__ = [
    # 主要类
    "AsyncHttpClient",
    
    # 配置类
    "RetryConfig",
    "TimeoutConfig", 
    "PoolConfig",
    "RequestMetrics",
    
    # 拦截器
    "RequestInterceptor",
    "LoggingInterceptor",
    "MetricsInterceptor",
    
    # 限流器
    "RateLimiter",
    
    # 工厂函数
    "create_http_client",
    
    # 全局函数
    "get",
    "post", 
    "put",
    "delete",
    "get_global_client",
    "close_global_client",
]
