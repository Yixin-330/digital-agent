# 系统设计

## 1. 总体架构

系统采用“感知层 + 记忆层 + 决策层 + 工具层 + 内容层”的分层架构。

核心链路：

```text
用户行为与环境信号
  -> Context 感知与状态识别
  -> Memory 与用户画像读取
  -> AI 决策与服务意图判断
  -> Tool Calling / Workflow 编排
  -> 内容生成、路线规划、任务触发、文创推荐
  -> 用户反馈与 Memory 更新
```

## 2. 主要系统模块

### 2.1 Client Experience Layer

面向用户的交互端。

可支持：

- 移动端小程序或 App。
- Web 导览端。
- 场馆屏幕或数字人终端。
- 语音助手。
- AR 或地图界面。

职责：

- 收集用户输入。
- 展示数字人回应。
- 展示地图、路线、任务与推荐。
- 采集用户行为事件。

### 2.2 Context Engine

负责实时上下文处理。

输入：

- location：当前位置、楼层、附近点位。
- time：当前时间、开放时间、剩余参观时间。
- behavior：停留、移动、点击、收藏、跳过、提问。
- session：当前目标、访问阶段、同行关系。
- environment：拥挤度、天气、活动、闭馆提醒。

输出：

- scene_type：如入口、展厅、休息区、出口、商店。
- user_state：如探索中、犹豫中、深入观看、赶时间、疲劳。
- trigger_candidates：可触发服务候选。
- context_summary：给模型使用的上下文摘要。

### 2.3 Memory Service

负责用户短期与长期记忆管理。

记忆分层：

- Session Memory：本次访问中即时有效的上下文。
- User Profile Memory：跨次访问保留的长期偏好。
- Interaction Memory：历史交互摘要。
- Preference Memory：稳定兴趣、表达风格、路线偏好。

关键能力：

- 读取相关记忆。
- 写入新偏好。
- 衰减过期偏好。
- 处理用户隐私授权。
- 区分事实、推断与临时状态。

### 2.4 Decision Orchestrator

负责判断下一步服务动作。

输入：

- 当前 Context。
- 用户 Memory。
- 可用工具列表。
- 场馆运营策略。
- 内容与商品数据。

输出：

- service_intent：讲解、推荐、规划、任务、提醒、文创等。
- action_plan：需要调用的工具顺序。
- response_policy：是否主动打扰、语气、长度、形式。

### 2.5 Tool Calling Layer

负责将智能体决策落到可执行能力。

建议工具：

- `search_cultural_knowledge`：检索景点、展品、人物、故事。
- `recommend_spots`：根据画像和当前位置推荐点位。
- `plan_route`：生成路线。
- `generate_explanation`：生成个性化讲解。
- `trigger_task`：触发互动任务。
- `recommend_products`：推荐文创商品。
- `update_user_memory`：更新用户画像。
- `log_event`：记录用户行为。

### 2.6 Content Knowledge Base

负责文化内容与业务内容管理。

数据类型：

- 景点与展品。
- 文化故事。
- 历史人物。
- 主题路线。
- 任务模板。
- 文创商品。
- 运营策略。

### 2.7 Analytics & Operations

负责运营分析与策略优化。

关注：

- 用户行为路径。
- 热点与冷点区域。
- 内容触达率。
- 任务完成率。
- 推荐转化。
- 主动服务效果。

## 3. 数据流设计

### 3.1 用户进入场景

```text
定位事件
  -> Context Engine 判断用户处于入口区域
  -> Memory Service 读取用户偏好
  -> Decision Orchestrator 判断是否生成访问建议
  -> recommend_spots / plan_route
  -> 数字人输出个性化开场与路线建议
```

### 3.2 用户停留较久

```text
停留事件
  -> Context Engine 判断为深度关注
  -> 检索点位内容
  -> 结合用户兴趣生成讲解
  -> 记录用户对主题的潜在偏好
```

### 3.3 用户完成互动任务

```text
任务完成事件
  -> log_event
  -> update_user_memory
  -> recommend_next_task 或 recommend_spots
  -> 生成鼓励反馈与下一步建议
```

## 4. Agent 决策循环

每次触发时，智能体可按以下循环工作：

1. Observe：读取用户输入和环境事件。
2. Understand：解析当前意图和 Context。
3. Recall：读取相关 Memory。
4. Decide：选择服务动作。
5. Act：调用工具或生成回应。
6. Reflect：根据反馈更新 Memory。

## 5. 服务触发策略

主动服务需要控制频率，避免打扰。

触发类型：

- 位置触发：靠近某点位。
- 时间触发：停留过久、接近闭馆、路线时间不足。
- 行为触发：重复查看、跳过、收藏、搜索。
- 兴趣触发：连续关注同一主题。
- 运营触发：活动推荐、分流提醒、重点展项曝光。

抑制条件：

- 用户刚拒绝主动推荐。
- 用户正在听讲解。
- 用户快速移动中。
- 短时间内已触发多次。
- 当前内容与用户偏好弱相关。

## 6. 技术选型建议

初期建议保持轻量：

- 前端：Web / 小程序 / React Native 任选其一。
- 后端：Python FastAPI 或 Node.js。
- 数据库：PostgreSQL。
- 向量检索：pgvector、Milvus 或 Qdrant。
- 缓存：Redis。
- 工作流：自研轻量 Orchestrator，后续可接 LangGraph 等框架。
- 地图：室外地图 API 或室内点位图。

## 7. 风险与约束

### 7.1 隐私风险

系统涉及位置、行为、偏好等敏感数据，需要提供授权、可查看、可删除机制。

### 7.2 主动服务打扰风险

主动推荐过多会降低体验。需要建立触发优先级、冷却时间和用户控制权。

### 7.3 内容准确性风险

文化讲解必须有知识库依据，避免模型幻觉。关键内容应采用检索增强生成，并保留来源。

### 7.4 冷启动问题

新用户缺少画像时，需要使用显式偏好选择、场景默认策略和轻量互动快速建立初始画像。
