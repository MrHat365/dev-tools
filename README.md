# Dev-Tools 🛠️

> **个人常用工具整理合集** - 既是一份知识积累，也是一份共享的开源资源

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/Code%20Style-PEP8-black.svg)](https://www.python.org/dev/peps/pep-0008/)

## 📋 项目简介

这是一个个人开发工具集合，涵盖了日常开发工作中常用的各类工具和组件。每个子项目都经过实际项目验证，具备生产环境使用的稳定性和可靠性。

### 🎯 项目目标

- **知识积累**: 整理和沉淀日常开发中的最佳实践
- **提高效率**: 提供可复用的工具组件，减少重复开发
- **开源共享**: 分享给更多开发者，共同提升开发体验
- **持续优化**: 根据实际使用反馈不断改进和完善

## 🗂️ 项目结构

```
dev-tools/
├── README.md              # 项目主文档
├── .gitignore            # Git忽略规则
├── http_client/          # 企业级异步HTTP客户端
│   ├── README.md         # 子项目文档
│   ├── requirements.txt  # 依赖包列表
│   ├── example_usage.py  # 使用示例
│   ├── http_client/      # 核心代码
│   │   ├── __init__.py
│   │   └── client.py     # 主要实现
│   └── logs/            # 日志目录
└── ...                  # 更多工具模块(待添加)
```

## 🔧 子项目介绍

### 1. HTTP Client - 企业级异步HTTP客户端

**位置**: `http_client/`  
**语言**: Python  
**依赖**: httpx, loguru, asyncio

#### 主要特性

- ✅ **高性能异步**: 基于httpx的异步HTTP客户端
- ✅ **智能重试**: 可配置的重试机制，支持指数退避
- ✅ **连接池管理**: 智能连接池配置和连接复用
- ✅ **请求限流**: 内置令牌桶算法，防止请求过载
- ✅ **拦截器系统**: 灵活的请求/响应拦截器架构
- ✅ **现代化日志**: 基于loguru的结构化日志系统
- ✅ **指标收集**: 自动收集请求时间、状态码等指标
- ✅ **错误处理**: 完善的异常处理和错误回调机制


详细文档请参考: [HTTP Client README](http_client/README.md)

### 2. 更多工具模块 (规划中)

以下工具模块正在开发或规划中:

- **Database Helper**: 数据库操作工具集
- **Redis Cache**: Redis缓存操作封装
- **Config Manager**: 配置管理工具
- **File Utils**: 文件操作工具集
- **Crypto Utils**: 加密解密工具
- **Email Sender**: 邮件发送工具
- **Task Queue**: 任务队列管理
- **API Validator**: API参数验证器

## 🤝 贡献指南

欢迎贡献代码和提出建议！

### 贡献方式

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

### 提交规范

- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 重构代码
- test: 测试相关
- chore: 构建工具或辅助工具的变动

## 📈 路线图

### v1.0 (当前)
- [x] HTTP Client - 企业级异步HTTP客户端
- [x] 项目文档和使用示例

### v1.1 (计划中)
- [ ] Database Helper - 数据库操作工具
- [ ] Redis Cache - Redis缓存封装
- [ ] 单元测试框架

### v1.2 (规划中)
- [ ] Config Manager - 配置管理
- [ ] File Utils - 文件操作工具
- [ ] 性能优化和监控工具


## 🙏 致谢

感谢以下开源项目的启发和支持:

- [httpx](https://github.com/encode/httpx) - 现代化的HTTP客户端
- [loguru](https://github.com/Delgan/loguru) - 优雅的日志库
- [asyncio](https://docs.python.org/3/library/asyncio.html) - Python异步编程
