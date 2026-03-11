#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== 正在停止自动化测试平台 ===${NC}"

# 1. 停止后台进程
if [ -f ".pids" ]; then
    echo "正在停止 FastAPI, Celery 和 Vite 进程..."
    while read pid; do
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            echo "已停止进程: $pid"
        fi
    done < .pids
    rm .pids
else
    echo "未找到 .pids 文件，尝试通过进程名停止..."
    pkill -f "uvicorn backend.main:app"
    pkill -f "celery -A backend.scheduler.celery_app"
    pkill -f "vite"
fi

# 2. 停止 Docker 容器
echo "正在停止 Docker 依赖服务 (MySQL, Redis)..."
docker-compose down

echo -e "${GREEN}=== 所有服务已停止 ===${NC}"
