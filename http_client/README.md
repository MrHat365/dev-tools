# 企业级异步HTTP客户端

基于httpx构建的企业级通用异步HTTP请求客户端，具备生产环境所需的完善功能。

## 功能特性

### 🚀 核心功能
- **异步支持**: 基于httpx的高性能异步HTTP客户端
- **连接池管理**: 智能连接池配置，支持连接复用和超时控制
- **自动重试**: 可配置的智能重试机制，支持指数退避
- **请求限流**: 内置令牌桶算法的请求限流器
- **拦截器系统**: 灵活的请求/响应拦截器架构

### 📊 监控与日志
- **Loguru日志系统**: 采用现代化的loguru日志库，支持结构化日志和丰富的格式化
- **请求指标收集**: 自动收集请求时间、状态码等指标
- **多级日志输出**: 支持控制台和文件双重输出，自动日志轮转和压缩
- **错误处理**: 完善的异常处理和错误回调机制

### 🔧 生产环境特性
- **超时控制**: 细粒度的连接、读取、写入超时配置
- **SSL验证**: 支持SSL证书验证控制
- **重定向处理**: 自动处理HTTP重定向
- **会话管理**: 支持异步上下文管理器

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 基础使用

```python
import asyncio
from http_client.client import create_http_client
from loguru import logger

async def main():
    # 创建客户端
    async with create_http_client(
        base_url="https://api.example.com",
        log_level="INFO"  # 设置日志级别
    ) as client:
        # GET请求
        response = await client.get("/users", params={"page": 1})
        logger.success(f"请求成功: {response.status_code}")
        
        # POST请求
        response = await client.post("/users", json_data={
            "name": "张三",
            "email": "zhangsan@example.com"
        })
        logger.info(f"创建用户: {response.status_code}")

asyncio.run(main())
```

### 日志配置

```python
from loguru import logger

# 配置loguru日志输出
logger.remove()  # 移除默认输出

# 添加控制台输出（带颜色）
logger.add(
    sink=lambda msg: print(msg, end=""),
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 添加文件输出（带轮转）
logger.add(
    sink="logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",    # 文件大小轮转
    retention="7 days",  # 保留时间
    compression="zip"    # 压缩格式
)
```

### 使用全局客户端

```python
from http_client.client import get, post, close_global_client
from loguru import logger

async def main():
    # 全局GET请求
    response = await get("https://httpbin.org/get")
    logger.success(f"GET请求: {response.status_code}")
    
    # 全局POST请求
    response = await post("https://httpbin.org/post", json_data={"key": "value"})
    logger.success(f"POST请求: {response.status_code}")
    
    # 关闭全局客户端
    await close_global_client()

asyncio.run(main())
```

## 高级配置

### 自定义配置

```python
from http_client.client import (
    AsyncHttpClient, RetryConfig, TimeoutConfig, 
    PoolConfig, RateLimiter
)

# 重试配置
retry_config = RetryConfig(
    max_retries=5,                              # 最大重试次数
    backoff_factor=0.5,                         # 退避因子
    retry_on_status=[500, 502, 503, 504, 429]   # 重试状态码
)

# 超时配置
timeout_config = TimeoutConfig(
    connect=5.0,    # 连接超时
    read=30.0,      # 读取超时
    write=30.0,     # 写入超时
    pool=5.0        # 连接池超时
)

# 连接池配置
pool_config = PoolConfig(
    max_keepalive_connections=20,   # 最大保持连接数
    max_connections=100,            # 最大连接数
    keepalive_expiry=5.0           # 连接保持时间
)

# 限流器（每秒最多10个请求）
rate_limiter = RateLimiter(max_requests=10, time_window=1.0)

# 创建客户端
client = AsyncHttpClient(
    base_url="https://api.example.com",
    headers={"User-Agent": "MyApp/1.0"},
    timeout_config=timeout_config,
    pool_config=pool_config,
    retry_config=retry_config,
    rate_limiter=rate_limiter
)
```

### 拦截器系统

#### 内置拦截器

```python
from http_client.client import LoggingInterceptor, MetricsInterceptor

# 日志拦截器（使用loguru）
logging_interceptor = LoggingInterceptor(log_level="DEBUG")

# 指标收集拦截器
metrics_interceptor = MetricsInterceptor()

client = AsyncHttpClient(
    interceptors=[logging_interceptor, metrics_interceptor]
)

# 获取指标
async with client:
    await client.get("/api/data")
    metrics = client.get_metrics()
    for metric in metrics:
        logger.info(f"{metric.method} {metric.url} - 耗时: {metric.response_time:.3f}s")
```

#### 自定义拦截器

```python
from http_client.client import RequestInterceptor
from loguru import logger

class AuthInterceptor(RequestInterceptor):
    """认证拦截器"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def before_request(self, request):
        """添加认证头"""
        request.headers["Authorization"] = f"Bearer {self.api_key}"
        logger.debug(f"添加认证头: {self.api_key[:8]}...")
        return request
    
    async def after_response(self, response):
        """处理响应"""
        if response.status_code == 401:
            logger.warning("认证失败，需要刷新token")
        return response
    
    async def on_error(self, error):
        """处理错误"""
        logger.error(f"请求错误: {error}")

# 使用自定义拦截器
client = AsyncHttpClient(
    interceptors=[AuthInterceptor("your-api-key")]
)
```

## 并发请求

```python
import asyncio
from loguru import logger

async def concurrent_requests():
    async with create_http_client(max_connections=20, log_level="WARNING") as client:
        # 创建并发任务
        tasks = [
            client.get(f"/api/data/{i}") 
            for i in range(10)
        ]
        
        # 并发执行
        logger.info("开始并发请求...")
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        success_count = sum(1 for r in responses if not isinstance(r, Exception))
        logger.success(f"并发请求完成: 成功 {success_count}, 失败 {len(responses) - success_count}")
```

## 错误处理

```python
from httpx import HTTPStatusError, RequestError
from loguru import logger

async def error_handling_example():
    async with create_http_client(max_retries=3, log_level="DEBUG") as client:
        try:
            response = await client.get("/api/data")
            response.raise_for_status()  # 抛出HTTP错误
        except HTTPStatusError as e:
            logger.error(f"HTTP错误: {e.response.status_code}")
        except RequestError as e:
            logger.error(f"请求错误: {e}")
        except Exception as e:
            logger.exception(f"未知错误: {e}")  # loguru的exception方法会自动包含堆栈信息
```

## 生产环境最佳实践

### 1. 日志配置

```python
from loguru import logger

# 生产环境日志配置
logger.remove()

# 错误和以上级别输出到控制台
logger.add(
    sink=lambda msg: print(msg, end=""),
    level="WARNING",
    format="<red>{time:YYYY-MM-DD HH:mm:ss}</red> | <level>{level}</level> | {message}"
)

# 所有日志输出到文件
logger.add(
    sink="logs/app.log",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8"
)

# 错误日志单独文件
logger.add(
    sink="logs/error.log",
    level="ERROR",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}\n{exception}",
    rotation="10 MB",
    retention="90 days",
    compression="zip"
)
```

### 2. 使用连接池

```python
# 推荐配置
client = create_http_client(
    max_connections=100,        # 根据服务器承载能力调整
    timeout_seconds=30.0,       # 合理的超时时间
    max_retries=3,             # 适度的重试次数
    enable_logging=True,        # 生产环境启用日志
    enable_metrics=True,        # 启用指标收集
    log_level="INFO"           # 适当的日志级别
)
```

### 3. 监控和指标

```python
async def monitor_requests():
    async with create_http_client(enable_metrics=True) as client:
        # 执行请求
        await client.get("/api/health")
        
        # 获取指标
        metrics = client.get_metrics()
        
        # 分析性能
        if metrics:
            avg_time = sum(m.response_time for m in metrics) / len(metrics)
            error_count = sum(1 for m in metrics if m.error)
            
            logger.info(f"平均响应时间: {avg_time:.3f}s")
            logger.info(f"错误率: {error_count/len(metrics)*100:.1f}%")
            
            # 性能告警
            if avg_time > 2.0:
                logger.warning(f"响应时间过长: {avg_time:.3f}s")
            if error_count / len(metrics) > 0.1:
                logger.error(f"错误率过高: {error_count/len(metrics)*100:.1f}%")
```

## 配置参数说明

### create_http_client() 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `base_url` | str | None | 基础URL |
| `max_retries` | int | 3 | 最大重试次数 |
| `timeout_seconds` | float | 30.0 | 超时时间（秒） |
| `max_connections` | int | 100 | 最大连接数 |
| `enable_logging` | bool | True | 是否启用日志 |
| `enable_metrics` | bool | True | 是否启用指标收集 |
| `log_level` | str | "INFO" | 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `rate_limit` | tuple | None | 限流配置 (请求数, 时间窗口) |

### 日志级别说明

- **DEBUG**: 详细的调试信息，包括所有请求和响应详情
- **INFO**: 一般信息，包括请求开始和完成状态
- **WARNING**: 警告信息，如重试、响应异常等
- **ERROR**: 错误信息，如请求失败、网络异常等
- **CRITICAL**: 严重错误，如系统级别的问题

## 运行示例

```bash
python example_usage.py
```

这将运行包含各种使用场景的完整示例，并在 `logs/` 目录下生成日志文件。

## 注意事项

1. **日志文件管理**: loguru会自动处理日志轮转和压缩，但需要定期清理旧日志
2. **日志级别**: 生产环境建议使用INFO或WARNING级别，避免DEBUG级别产生过多日志
3. **性能影响**: 过多的日志输出可能影响性能，合理配置日志级别
4. **异常追踪**: 使用 `logger.exception()` 可以自动记录完整的异常堆栈
5. **结构化日志**: loguru支持JSON格式输出，便于日志分析系统处理

## 许可证

MIT License 