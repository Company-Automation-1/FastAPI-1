
# 项目结构

```bash
    project-1/
    ├── api/                 # API接口层
    │   └── v1/             # API版本1
    │       ├── device.py   # 设备相关接口
    │       └── upload.py   # 上传相关接口
    ├── core/               # 核心功能模块
    │   ├── config.py      # 配置文件
    │   ├── scheduler.py   # 任务调度器
    │   └── tasks.py       # 任务定义
    ├── models/            # 数据模型
    │   └── request.py    # 请求数据模型
    ├── services/         # 业务逻辑层
    │   └── upload_service.py  # 上传业务处理
    ├── utils/            # 工具函数
    │   └── file_utils.py    # 文件处理工具
    └── main.py          # 应用入口
```
