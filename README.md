# Auto-Test Platform (自动化测试平台)

基于 Python (FastAPI + pytest) 和 Vue 3 构建的轻量级接口自动化测试平台。专为测试人员设计，主打“零代码”的 YAML 驱动测试体验。

## 🌟 核心特性

- **可视化编排**: 提供友好的 Web 界面，在线管理和编排测试用例。
- **YAML 驱动**: 测试人员无需编写 Python 代码，只需编写直观的 YAML 即可完成接口测试和断言。
- **异步调度**: 基于 Celery + Redis 实现测试任务的异步下发与执行。
- **精美报告**: 深度集成 Allure，提供详细的请求/响应日志和测试报告。
- **用例自动生成**: 内置工具支持将 Swagger/OpenAPI 文档或 HAR 抓包文件一键转换为 YAML 用例。
- **CI/CD 友好**: 提供标准的 GitHub Actions 配置文件，支持自动化触发与钉钉/企微消息通知。

## 🏗 系统架构

```text
           自动化测试平台

      ┌───────────────────┐
      │   Web管理后台     │  <-- Vue 3 + Element Plus
      │  (测试人员操作)    │
      └────────┬──────────┘
               │ HTTP API
               ▼
      ┌───────────────────┐
      │   FastAPI 后端    │  <-- 接口服务 + MySQL
      └────────┬──────────┘
               │ Celery
               ▼
      ┌───────────────────┐
      │   任务调度系统    │  <-- Redis
      └────────┬──────────┘
               │ 
               ▼
      ┌───────────────────┐
      │  Python测试引擎   │  <-- pytest + requests + yaml
      └────────┬──────────┘
               │
               ▼
      ┌───────────────────┐
      │   Allure报告系统  │  <-- 静态 HTML 报告
      └───────────────────┘
```

## 🚀 快速启动

我们提供了一键启动脚本，可以快速在本地拉起整个平台。

### 1. 环境准备
- **Python 3.9+**
- **Node.js 18+**
- **Docker & Docker Compose** (用于启动 MySQL 和 Redis)
- **Allure 命令行工具** (用于生成报告，Mac: `brew install allure`)

### 2. 一键启动
在项目根目录下运行：
```bash
./start.sh
```
该脚本会自动：
1. 启动 MySQL 和 Redis 容器。
2. 安装 Python 依赖并启动 FastAPI 后端服务 (端口 `8006`)。
3. 启动 Celery Worker 处理测试任务。
4. 安装前端依赖并启动 Vue 3 开发服务器 (端口 `3006`)。

启动成功后，访问：[http://localhost:3006](http://localhost:3006)

### 3. 一键停止
```bash
./stop.sh
```

## 📝 YAML 用例编写指南

用例采用极简的 YAML 格式，支持丰富的断言机制。

### 基础示例
```yaml
name: 用户登录测试
request:
  method: POST
  url: https://httpbin.org/post
  json:
    username: test
    password: 123456
validate:
  - eq:
      status_code: 200
  - contains:
      body.json.username: test
```

### 断言规则 (Validate)
- `eq`: 相等断言。可以断言 `status_code`，或通过 `body.xxx.yyy` 的 JSON Path 语法提取响应体字段进行断言。
- `contains`: 包含断言。判断响应内容中是否包含指定字符串。
- `in`: 列表包含断言。判断实际值是否在预期列表中，如 `status_code: [200, 201]`。

## 🛠 自动化用例生成工具

为了进一步降低编写成本，项目 `tools/` 目录下提供了自动生成脚本：

1. **OpenAPI 转 YAML**:
   ```bash
   python tools/openapi_to_yaml.py swagger.json output_cases.yaml
   ```
2. **HAR 抓包转 YAML**:
   ```bash
   python tools/har_to_yaml.py traffic.har output_cases.yaml
   ```

## 🔄 CI/CD 集成

项目内置了 `.github/workflows/test.yml`。
当代码推送到 `main` 分支或定时触发时，GitHub Actions 会：
1. 自动拉起环境并执行所有测试引擎下的用例。
2. 生成 Allure 报告并部署到 GitHub Pages。
3. 调用 `tools/notify.py` 将测试结果和报告链接推送到钉钉/企业微信群。

*(注：需在 GitHub 仓库的 Secrets 中配置 `DINGTALK_WEBHOOK`)*
