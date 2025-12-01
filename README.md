# iOS AI 健康管理后端（Python Demo）

一个基于 Python/FastAPI 的参考实现，用于承载需求文档描述的健康管理能力：

- AI 大模型接入与个性化建议（提供规则兜底，可替换为真实 LLM 服务）。
- HealthKit 数据同步接口、手动录入、趋势预警、睡眠/饮食/运动建议。
- 对话式健康助手、用户反馈、社交分享入口。
- 登录鉴权（Apple ID/Google/X）、订阅配额（免费 3 次/天，订阅无限制）、背景模式切换。

## 快速开始

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动后访问 `http://127.0.0.1:8000/docs` 查看交互式接口文档。

## 核心端点

- `POST /health-data/sync`：同步 HealthKit 数据并返回即时建议。
- `POST /manual-entry`：手动录入运动/睡眠/心率等数据并获取建议。
- `GET /health-data/{user_id}`：查看用户所有健康记录（自动与手动）。
- `POST /chat`：对话式健康助手。
- `POST /trends`：提交趋势变化（如睡眠下降、心率上升）获取预警。
- `POST /feedback`：提交满意度和文字反馈。
- `POST /social/share`：生成社交分享记录，便于后续通知或推送。
- `GET /stats`：查看示例存储中的用户数量。
- `POST /auth/login`：模拟 Apple/Google/X 登录，返回 `user_id` 与订阅信息。
- `POST /subscription`：设置订阅等级（free/monthly/quarterly/yearly），对应价格：$14.9/月、$39.9/季度、$150/年。
- `POST /settings/background`：设置背景模式（light/dark/system），供客户端同步。

> 免费用户每天仅可触发 3 次分析（HealthKit 同步或手动录入均计数），订阅后不限次数。

## 结构说明

- `app/ai_engine.py`：AI 处理入口，可在 `_llm_generate` 中替换为真实大模型调用。
- `app/storage.py`：内存存储，用于演示数据流。生产环境可换为数据库/云存储。
- `app/schemas.py`：Pydantic 数据模型，包含输入校验（心率区间、步数非负等）。
- `app/api.py`：REST 接口实现，串联存储与 AI 引擎。
- `app/main.py`：FastAPI 入口，供 `uvicorn` 启动。

## 与 iOS 客户端对接提示

- HealthKit 读取的数据通过 JSON 提交到 `/health-data/sync`，示例字段：
  ```json
  {
    "user_id": "demo-user",
    "steps": 6200,
    "resting_heart_rate": 62,
    "active_minutes": 35,
    "sleep_hours": 7.3,
    "timestamp": "2024-06-04T10:05:00Z"
  }
  ```
- 对话接口 `/chat` 可以携带历史上下文由后端保留，实现多轮问答。
- 趋势分析可由客户端统计周同比变化后提交到 `/trends` 获取预警提示。

该示例聚焦于 API 设计和数据流演示，可根据需要替换模型、存储和鉴权方案。
