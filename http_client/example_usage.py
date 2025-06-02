#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
HTTP客户端使用示例
演示如何使用企业级异步HTTP客户端
"""

import asyncio
from loguru import logger
from http_client.client import (
    AsyncHttpClient, 
    create_http_client,
    RetryConfig, 
    TimeoutConfig, 
    PoolConfig,
    LoggingInterceptor,
    MetricsInterceptor,
    RateLimiter,
    get, post, put, delete, close_global_client
)

# 配置loguru日志
logger.remove()  # 移除默认的控制台输出
logger.add(
    sink=lambda msg: print(msg, end=""),  # 输出到控制台
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    sink="logs/http_client.log",  # 输出到文件
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",  # 文件大小超过10MB时轮转
    retention="7 days",  # 保留7天的日志
    compression="zip"  # 压缩旧日志文件
)


async def basic_usage_example():
    """基础使用示例"""
    logger.info("=== 基础使用示例 ===")
    
    # 使用便捷工厂函数创建客户端
    async with create_http_client(
        base_url="https://httpbin.org",
        timeout_seconds=10.0,
        max_retries=2,
        log_level="INFO"
    ) as client:
        # GET请求
        response = await client.get("/get", params={"key": "value"})
        logger.success(f"GET响应状态: {response.status_code}")
        logger.debug(f"GET响应内容: {response.json()}")
        
        # POST请求
        response = await client.post("/post", json_data={"name": "张三", "age": 30})
        logger.success(f"POST响应状态: {response.status_code}")
        
        # PUT请求
        response = await client.put("/put", json_data={"update": "数据更新"})
        logger.success(f"PUT响应状态: {response.status_code}")
        
        # DELETE请求
        response = await client.delete("/delete")
        logger.success(f"DELETE响应状态: {response.status_code}")


async def advanced_configuration_example():
    """高级配置示例"""
    logger.info("\n=== 高级配置示例 ===")
    
    # 自定义配置
    retry_config = RetryConfig(
        max_retries=5,
        backoff_factor=0.5,
        retry_on_status=[500, 502, 503, 504, 429]
    )
    
    timeout_config = TimeoutConfig(
        connect=3.0,
        read=15.0,
        write=15.0,
        pool=3.0
    )
    
    pool_config = PoolConfig(
        max_keepalive_connections=10,
        max_connections=50,
        keepalive_expiry=30.0
    )
    
    # 创建限流器（每秒最多10个请求）
    rate_limiter = RateLimiter(max_requests=10, time_window=1.0)
    
    # 创建拦截器
    interceptors = [
        LoggingInterceptor(log_level="DEBUG"),
        MetricsInterceptor()
    ]
    
    # 创建自定义客户端
    client = AsyncHttpClient(
        base_url="https://httpbin.org",
        headers={"User-Agent": "MyApp/1.0"},
        timeout_config=timeout_config,
        pool_config=pool_config,
        retry_config=retry_config,
        interceptors=interceptors,
        rate_limiter=rate_limiter,
        verify_ssl=True,
        follow_redirects=True
    )
    
    async with client:
        # 批量请求测试限流
        tasks = []
        for i in range(5):
            task = client.get(f"/delay/1?request={i}")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        logger.success(f"批量请求完成，共{len(responses)}个响应")
        
        # 获取指标
        metrics = client.get_metrics()
        logger.info(f"请求指标数量: {len(metrics)}")
        for metric in metrics:
            logger.info(f"  {metric.method} {metric.url} - "
                      f"状态: {metric.status_code}, "
                      f"耗时: {metric.response_time:.3f}s")


async def error_handling_example():
    """错误处理示例"""
    logger.info("\n=== 错误处理示例 ===")
    
    async with create_http_client(max_retries=2, log_level="WARNING") as client:
        try:
            # 测试404错误
            response = await client.get("https://httpbin.org/status/404")
        except Exception as e:
            logger.error(f"404错误处理: {e}")
        
        try:
            # 测试500错误（会自动重试）
            response = await client.get("https://httpbin.org/status/500")
        except Exception as e:
            logger.error(f"500错误处理（重试后）: {e}")
        
        try:
            # 测试超时
            response = await client.get("https://httpbin.org/delay/100")
        except Exception as e:
            logger.error(f"超时错误处理: {e}")


async def custom_interceptor_example():
    """自定义拦截器示例"""
    logger.info("\n=== 自定义拦截器示例 ===")
    
    class AuthInterceptor(LoggingInterceptor):
        """认证拦截器"""
        
        def __init__(self, api_key: str):
            super().__init__(log_level="DEBUG")
            self.api_key = api_key
        
        async def before_request(self, request):
            """添加认证头"""
            request.headers["Authorization"] = f"Bearer {self.api_key}"
            await super().before_request(request)
            return request
    
    class ResponseValidationInterceptor(LoggingInterceptor):
        """响应验证拦截器"""
        
        def __init__(self):
            super().__init__(log_level="DEBUG")
        
        async def after_response(self, response):
            """验证响应"""
            if response.status_code >= 400:
                logger.warning(f"响应异常: {response.status_code}")
            await super().after_response(response)
            return response
    
    # 使用自定义拦截器
    client = AsyncHttpClient(
        base_url="https://httpbin.org",
        interceptors=[
            AuthInterceptor("your-api-key-here"),
            ResponseValidationInterceptor(),
            MetricsInterceptor()
        ]
    )
    
    async with client:
        response = await client.get("/headers")
        logger.success(f"带认证的请求完成: {response.status_code}")
        
        # 获取并显示指标
        metrics = client.get_metrics()
        if metrics:
            latest_metric = metrics[-1]
            logger.info(f"最新指标: {latest_metric.method} {latest_metric.url} "
                      f"耗时: {latest_metric.response_time:.3f}s")


async def concurrent_requests_example():
    """并发请求示例"""
    logger.info("\n=== 并发请求示例 ===")
    
    async with create_http_client(
        base_url="https://httpbin.org",
        max_connections=20,
        log_level="WARNING"  # 减少日志输出
    ) as client:
        # 创建大量并发请求
        tasks = []
        for i in range(10):
            task = client.get(f"/delay/1?id={i}")
            tasks.append(task)
        
        logger.info("开始并发请求...")
        start_time = asyncio.get_event_loop().time()
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = asyncio.get_event_loop().time()
        logger.success(f"并发请求完成，总耗时: {end_time - start_time:.2f}秒")
        
        # 统计结果
        success_count = sum(1 for r in responses if not isinstance(r, Exception))
        error_count = len(responses) - success_count
        logger.info(f"成功: {success_count}, 失败: {error_count}")


async def global_client_example():
    """全局客户端示例"""
    logger.info("\n=== 全局客户端示例 ===")
    
    # 使用全局便捷函数
    try:
        response = await get("https://httpbin.org/get")
        logger.success(f"全局GET请求: {response.status_code}")
        
        response = await post("https://httpbin.org/post", json_data={"test": "全局POST"})
        logger.success(f"全局POST请求: {response.status_code}")
        
    finally:
        # 记得关闭全局客户端
        await close_global_client()


async def main():
    """主函数"""
    logger.info("企业级异步HTTP客户端使用示例")
    logger.info("=" * 50)
    
    # 运行各种示例
    await basic_usage_example()
    await advanced_configuration_example()
    await error_handling_example()
    await custom_interceptor_example()
    await concurrent_requests_example()
    await global_client_example()
    
    logger.success("\n示例执行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main()) 