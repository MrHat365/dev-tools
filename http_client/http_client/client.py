#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：api 
@Author  ：Mr.Hat
@Date    ：2025/6/2 18:38 
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, Union, Tuple
from dataclasses import dataclass, field
from urllib.parse import urljoin
import httpx
from httpx import AsyncClient, Response, RequestError
from loguru import logger


@dataclass
class RetryConfig:
    """重试配置类"""
    max_retries: int = 3  # 最大重试次数
    backoff_factor: float = 0.3  # 退避因子
    retry_on_status: List[int] = field(default_factory=lambda: [500, 502, 503, 504])  # 需要重试的状态码
    retry_on_exceptions: List[type[Exception]] = field(default_factory=lambda: [RequestError])  # 需要重试的异常类型


@dataclass
class TimeoutConfig:
    """超时配置类"""
    connect: float = 5.0  # 连接超时
    read: float = 30.0  # 读取超时
    write: float = 30.0  # 写入超时
    pool: float = 5.0  # 连接池超时


@dataclass
class PoolConfig:
    """连接池配置类"""
    max_keepalive_connections: int = 20  # 最大保持连接数
    max_connections: int = 100  # 最大连接数
    keepalive_expiry: float = 5.0  # 连接保持时间


@dataclass
class RequestMetrics:
    """请求指标类"""
    url: str
    method: str
    status_code: Optional[int] = None
    response_time: Optional[float] = None
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


class RequestInterceptor:
    """请求拦截器基类"""
    
    async def before_request(self, request: httpx.Request) -> httpx.Request:
        """请求前拦截"""
        return request
    
    async def after_response(self, response: httpx.Response) -> httpx.Response:
        """响应后拦截"""
        return response
    
    async def on_error(self, error: Exception) -> None:
        """错误拦截"""
        pass
        return


class LoggingInterceptor(RequestInterceptor):
    """日志拦截器"""
    
    def __init__(self, log_level: str = "INFO"):
        """
        初始化日志拦截器
        
        Args:
            log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_level = log_level.upper()
    
    async def before_request(self, request: httpx.Request) -> httpx.Request:
        """记录请求日志"""
        logger.log(self.log_level, f"发起请求: {request.method} {request.url}")
        return request
    
    async def after_response(self, response: httpx.Response) -> httpx.Response:
        """记录响应日志"""
        logger.log(self.log_level, f"收到响应: {response.status_code} {response.url} "
                  f"耗时: {response.elapsed.total_seconds():.3f}s")
        return response
    
    async def on_error(self, error: Exception) -> None:
        """记录错误日志"""
        logger.error(f"请求异常: {error}")
        return


class MetricsInterceptor(RequestInterceptor):
    """指标收集拦截器"""
    
    def __init__(self):
        self.metrics: List[RequestMetrics] = []
        self._start_time = None
    
    async def before_request(self, request: httpx.Request) -> httpx.Request:
        """开始计时"""
        self._start_time = time.time()
        return request
    
    async def after_response(self, response: httpx.Response) -> httpx.Response:
        """收集成功指标"""
        if self._start_time:
            response_time = time.time() - self._start_time
            metric = RequestMetrics(
                url=str(response.url),
                method=response.request.method,
                status_code=response.status_code,
                response_time=response_time
            )
            self.metrics.append(metric)
        return response
    
    async def on_error(self, error: Exception) -> None:
        """收集错误指标"""
        if self._start_time and hasattr(error, 'request'):
            response_time = time.time() - self._start_time
            metric = RequestMetrics(
                url=str(error.request.url),
                method=error.request.method,
                response_time=response_time,
                error=str(error)
            )
            self.metrics.append(metric)
        return


class RateLimiter:
    """请求限流器"""
    
    def __init__(self, max_requests: int, time_window: float = 1.0):
        """
        初始化限流器
        
        Args:
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """获取请求许可"""
        async with self._lock:
            now = time.time()
            # 清理过期的请求记录
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            # 检查是否超过限制
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                    return await self.acquire()
            
            self.requests.append(now)
            return None


class AsyncHttpClient:
    """企业级异步HTTP客户端"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout_config: Optional[TimeoutConfig] = None,
        pool_config: Optional[PoolConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        interceptors: Optional[List[RequestInterceptor]] = None,
        rate_limiter: Optional[RateLimiter] = None,
        verify_ssl: bool = True,
        follow_redirects: bool = True
    ):
        """
        初始化HTTP客户端
        
        Args:
            base_url: 基础URL
            headers: 默认请求头
            timeout_config: 超时配置
            pool_config: 连接池配置
            retry_config: 重试配置
            interceptors: 拦截器列表
            rate_limiter: 限流器
            verify_ssl: 是否验证SSL证书
            follow_redirects: 是否跟随重定向
        """
        self.base_url = base_url
        self.default_headers = headers or {}
        self.timeout_config = timeout_config or TimeoutConfig()
        self.pool_config = pool_config or PoolConfig()
        self.retry_config = retry_config or RetryConfig()
        self.interceptors = interceptors or []
        self.rate_limiter = rate_limiter
        self.verify_ssl = verify_ssl
        self.follow_redirects = follow_redirects
        
        # 创建httpx客户端配置
        self._client: Optional[AsyncClient] = None
        self._session_started = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close_session()
    
    async def start_session(self) -> None:
        """启动会话"""
        if not self._session_started:
            # 构建超时配置
            timeout = httpx.Timeout(
                connect=self.timeout_config.connect,
                read=self.timeout_config.read,
                write=self.timeout_config.write,
                pool=self.timeout_config.pool
            )
            
            # 构建连接池限制
            limits = httpx.Limits(
                max_keepalive_connections=self.pool_config.max_keepalive_connections,
                max_connections=self.pool_config.max_connections,
                keepalive_expiry=self.pool_config.keepalive_expiry
            )
            
            # 创建客户端
            self._client = AsyncClient(
                base_url=self.base_url,
                timeout=timeout,
                limits=limits,
                verify=self.verify_ssl,
                follow_redirects=self.follow_redirects
            )
            self._session_started = True
            logger.info("HTTP客户端会话已启动")
        return
    
    async def close_session(self) -> None:
        """关闭会话"""
        if self._client and self._session_started:
            await self._client.aclose()
            self._session_started = False
            logger.info("HTTP客户端会话已关闭")
        return
    
    def _merge_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """合并请求头"""
        merged = self.default_headers.copy()
        if headers:
            merged.update(headers)
        return merged
    
    def _build_url(self, url: str) -> str:
        """构建完整URL"""
        if self.base_url and not url.startswith(('http://', 'https://')):
            return urljoin(self.base_url, url)
        return url
    
    async def _apply_interceptors_before(self, request: httpx.Request) -> httpx.Request:
        """应用请求前拦截器"""
        for interceptor in self.interceptors:
            request = await interceptor.before_request(request)
        return request
    
    async def _apply_interceptors_after(self, response: httpx.Response) -> httpx.Response:
        """应用响应后拦截器"""
        for interceptor in self.interceptors:
            response = await interceptor.after_response(response)
        return response
    
    async def _apply_interceptors_error(self, error: Exception) -> None:
        """应用错误拦截器"""
        for interceptor in self.interceptors:
            await interceptor.on_error(error)
        return
    
    async def _should_retry(self, attempt: int, response: Optional[Response], 
                          exception: Optional[Exception]) -> bool:
        """判断是否应该重试"""
        if attempt >= self.retry_config.max_retries:
            return False
        
        # 检查状态码重试
        if response and response.status_code in self.retry_config.retry_on_status:
            return True
        
        # 检查异常重试
        if exception:
            for retry_exception in self.retry_config.retry_on_exceptions:
                if isinstance(exception, retry_exception):
                    return True
        
        return False
    
    async def _calculate_backoff(self, attempt: int) -> float:
        """计算退避时间"""
        return self.retry_config.backoff_factor * (2 ** attempt)
    
    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Response:
        """带重试的请求"""
        if not self._session_started:
            await self.start_session()
        
        # 应用限流
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        last_exception = None
        last_response = None
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                # 发起请求
                response = await self._client.request(method, url, **kwargs)
                
                # 应用响应后拦截器
                response = await self._apply_interceptors_after(response)
                
                # 检查是否需要重试
                if not await self._should_retry(attempt, response, None):
                    response.raise_for_status()  # 抛出HTTP错误
                    return response
                
                last_response = response
                
            except Exception as e:
                last_exception = e
                await self._apply_interceptors_error(e)
                
                # 检查是否需要重试
                if not await self._should_retry(attempt, None, e):
                    raise e
            
            # 如果不是最后一次尝试，则等待后重试
            if attempt < self.retry_config.max_retries:
                backoff_time = await self._calculate_backoff(attempt)
                logger.warning(f"请求失败，{backoff_time:.2f}秒后重试 (第{attempt + 1}次)")
                await asyncio.sleep(backoff_time)
        
        # 所有重试都失败了
        if last_exception:
            raise last_exception
        if last_response:
            last_response.raise_for_status()
            return last_response
        
        raise RuntimeError("请求失败：未知错误")
    
    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        files: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Response:
        """
        发起HTTP请求
        
        Args:
            method: 请求方法
            url: 请求URL
            params: URL参数
            headers: 请求头
            json_data: JSON数据
            data: 请求体数据
            files: 文件数据
            **kwargs: 其他参数
        
        Returns:
            httpx.Response: 响应对象
        """
        # 构建完整URL
        full_url = self._build_url(url)
        
        # 合并请求头
        merged_headers = self._merge_headers(headers)
        
        # 构建请求参数
        request_kwargs = {
            'params': params,
            'headers': merged_headers,
            'files': files,
            **kwargs
        }
        
        # 处理请求体数据
        if json_data is not None:
            request_kwargs['json'] = json_data
        elif data is not None:
            request_kwargs['data'] = data
        
        return await self._request_with_retry(method, full_url, **request_kwargs)
    
    async def get(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """GET请求"""
        return await self.request('GET', url, params=params, headers=headers, **kwargs)
    
    async def post(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """POST请求"""
        return await self.request('POST', url, json_data=json_data, data=data, headers=headers, **kwargs)
    
    async def put(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """PUT请求"""
        return await self.request('PUT', url, json_data=json_data, data=data, headers=headers, **kwargs)
    
    async def patch(
        self,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """PATCH请求"""
        return await self.request('PATCH', url, json_data=json_data, data=data, headers=headers, **kwargs)
    
    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """DELETE请求"""
        return await self.request('DELETE', url, headers=headers, **kwargs)
    
    async def head(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """HEAD请求"""
        return await self.request('HEAD', url, headers=headers, **kwargs)
    
    async def options(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Response:
        """OPTIONS请求"""
        return await self.request('OPTIONS', url, headers=headers, **kwargs)
    
    def add_interceptor(self, interceptor: RequestInterceptor) -> None:
        """添加拦截器"""
        self.interceptors.append(interceptor)
        return
    
    def remove_interceptor(self, interceptor: RequestInterceptor) -> None:
        """移除拦截器"""
        if interceptor in self.interceptors:
            self.interceptors.remove(interceptor)
        return
    
    def get_metrics(self) -> List[RequestMetrics]:
        """获取请求指标"""
        metrics = []
        for interceptor in self.interceptors:
            if isinstance(interceptor, MetricsInterceptor):
                metrics.extend(interceptor.metrics)
        return metrics


# 便捷的工厂函数
def create_http_client(
    base_url: Optional[str] = None,
    max_retries: int = 3,
    timeout_seconds: float = 30.0,
    max_connections: int = 100,
    enable_logging: bool = True,
    enable_metrics: bool = True,
    log_level: str = "INFO",
    rate_limit: Optional[Tuple[int, float]] = None,
    **kwargs
) -> AsyncHttpClient:
    """
    创建HTTP客户端的便捷工厂函数
    
    Args:
        base_url: 基础URL
        max_retries: 最大重试次数
        timeout_seconds: 超时时间
        max_connections: 最大连接数
        enable_logging: 是否启用日志
        enable_metrics: 是否启用指标收集
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rate_limit: 限流配置 (max_requests, time_window)
        **kwargs: 其他参数
    
    Returns:
        AsyncHttpClient: HTTP客户端实例
    """
    # 配置超时
    timeout_config = TimeoutConfig(
        connect=5.0,
        read=timeout_seconds,
        write=timeout_seconds,
        pool=5.0
    )
    
    # 配置连接池
    pool_config = PoolConfig(max_connections=max_connections)
    
    # 配置重试
    retry_config = RetryConfig(max_retries=max_retries)
    
    # 配置拦截器
    interceptors = []
    if enable_logging:
        interceptors.append(LoggingInterceptor(log_level=log_level))
    if enable_metrics:
        interceptors.append(MetricsInterceptor())
    
    # 配置限流器
    rate_limiter = None
    if rate_limit:
        rate_limiter = RateLimiter(rate_limit[0], rate_limit[1])
    
    return AsyncHttpClient(
        base_url=base_url,
        timeout_config=timeout_config,
        pool_config=pool_config,
        retry_config=retry_config,
        interceptors=interceptors,
        rate_limiter=rate_limiter,
        **kwargs
    )


# 全局客户端实例（可选）
_global_client: Optional[AsyncHttpClient] = None


async def get_global_client() -> AsyncHttpClient:
    """获取全局HTTP客户端实例"""
    global _global_client
    if _global_client is None:
        _global_client = create_http_client()
        await _global_client.start_session()
    return _global_client


async def close_global_client() -> None:
    """关闭全局HTTP客户端"""
    global _global_client
    if _global_client:
        await _global_client.close_session()
        _global_client = None
    return


# 便捷的全局请求函数
async def get(url: str, **kwargs) -> Response:
    """全局GET请求"""
    client = await get_global_client()
    return await client.get(url, **kwargs)


async def post(url: str, **kwargs) -> Response:
    """全局POST请求"""
    client = await get_global_client()
    return await client.post(url, **kwargs)


async def put(url: str, **kwargs) -> Response:
    """全局PUT请求"""
    client = await get_global_client()
    return await client.put(url, **kwargs)


async def delete(url: str, **kwargs) -> Response:
    """全局DELETE请求"""
    client = await get_global_client()
    return await client.delete(url, **kwargs)
