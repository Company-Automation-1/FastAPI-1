"""
应用程序入口模块

该模块是FastAPI应用程序的主入口，负责：
1. 配置和启动Web服务器
2. 注册路由和中间件
3. 管理应用程序生命周期事件

主要功能：
- 初始化FastAPI应用
- 配置日志系统
- 注册API路由
- 管理调度器的启动和关闭
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.upload import router as upload_router
from api.v1.device import router as device_router
from core.scheduler import start_scheduler, stop_scheduler

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

# 创建FastAPI应用实例
app = FastAPI(
    title="Device Data API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """
    应用程序启动时的处理函数
    
    启动调度器，确保能够处理定时任务
    """
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """
    应用程序关闭时的处理函数
    
    安全地关闭调度器，确保正在执行的任务能够完成
    """
    stop_scheduler()

# 注册路由
app.include_router(upload_router)
app.include_router(device_router)

# 启动服务器（仅在直接运行时）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)