#!/bin/bash

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 启动自动化测试平台 ===${NC}"

# 1. 启动基础服务 (MySQL, Redis)
echo -e "${YELLOW}[1/4] 启动 Docker 依赖服务 (MySQL, Redis)...${NC}"
docker-compose up -d
sleep 5 # 等待数据库初始化

# 2. 检查并创建 Python 虚拟环境
echo -e "${YELLOW}[2/4] 准备 Python 环境并启动后端服务...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt 2>/dev/null || pip install fastapi uvicorn sqlalchemy pymysql cryptography alembic celery redis pytest requests pyyaml allure-pytest pydantic croniter httpx python-multipart

# 启动 FastAPI 后端 (后台运行)
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8006 > backend.log 2>&1 &
BACKEND_PID=$!
echo "FastAPI 后端已启动 (PID: $BACKEND_PID, 端口: 8006)"

# 3. 启动 Celery Worker + Beat
echo -e "${YELLOW}[3/5] 启动 Celery 任务调度 Worker + Beat...${NC}"
nohup celery -A backend.scheduler.celery_app worker --loglevel=info > celery.log 2>&1 &
CELERY_PID=$!
echo "Celery Worker 已启动 (PID: $CELERY_PID)"

nohup celery -A backend.scheduler.celery_app beat --loglevel=info > celery-beat.log 2>&1 &
BEAT_PID=$!
echo "Celery Beat 已启动 (PID: $BEAT_PID)"

# 4. 启动前端服务
echo -e "${YELLOW}[4/5] 启动 Vue 3 前端服务...${NC}"
cd frontend
npm install
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "Vue 前端已启动 (PID: $FRONTEND_PID, 端口: 3006)"

# 保存 PID 以便后续停止
echo "$BACKEND_PID" > .pids
echo "$CELERY_PID" >> .pids
echo "$BEAT_PID" >> .pids
echo "$FRONTEND_PID" >> .pids

echo -e "\n${GREEN}=== 所有服务启动完成！ ===${NC}"
echo -e "前端访问地址: ${GREEN}http://localhost:3006${NC}"
echo -e "后端 API 文档: ${GREEN}http://localhost:8006/docs${NC}"
echo -e "你可以使用 ./stop.sh 来停止所有服务。"
