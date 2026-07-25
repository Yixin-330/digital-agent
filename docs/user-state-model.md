# 用户状态与 Memory 模型

## 1. 设计目标

用户状态模型用于回答三个问题：

1. 用户现在处于什么场景？
2. 用户当前可能需要什么服务？
3. 用户长期偏好如何影响这次决策？

系统需要同时处理短期状态和长期画像。

## 2. 用户状态分层

### 2.1 实时状态

来自当前位置、行为和即时交互。

字段示例：

```json
{
  "user_id": "u_001",
  "location": {
    "site_id": "museum_001",
    "area_id": "hall_02",
    "spot_id": "artifact_102",
    "confidence": 0.92
  },
  "visit_stage": "exploring",
  "dwell_time_seconds": 180,
  "movement_speed": "slow",
  "current_activity": "viewing",
  "last_interaction": "asked_question",
  "fatigue_signal": "unknown"
}
```

### 2.2 会话状态

本次访问中持续有效，但离开场景后可能失效。

字段示例：

```json
{
  "session_id": "s_001",
  "visit_goal": "deep_culture",
  "available_time_minutes": 90,
  "companions": "family",
  "selected_route": "history_story_route",
  "visited_spots": ["gate", "hall_01"],
  "skipped_spots": ["hall_03"],
  "active_tasks": ["find_dragon_pattern"],
  "recent_topics": ["architecture", "mythology"]
}
```

### 2.3 长期用户画像

跨会话保留，用于个性化推荐。

字段示例：

```json
{
  "user_id": "u_001",
  "interest_profile": {
    "history": 0.82,
    "architecture": 0.74,
    "craft": 0.51,
    "celebrity_story": 0.34,
    "shopping": 0.42
  },
  "content_style": {
    "preferred_length": "medium",
    "tone": "storytelling",
    "interaction_level": "high"
  },
  "route_preference": {
    "pace": "slow",
    "avoid_crowd": true,
    "likes_hidden_spots": true
  },
  "commerce_preference": {
    "accepts_cultural_products": true,
    "preferred_categories": ["books", "crafts"]
  }
}
```

## 3. Context 信号

### 3.1 位置类信号

- 当前场馆、区域、点位。
- 与重点点位的距离。
- 是否接近出口、商店、休息区。
- 是否进入拥挤区域。

### 3.2 行为类信号

- 停留时长。
- 移动速度。
- 点击、收藏、分享、跳过。
- 是否重复查看同一主题。
- 是否完成任务。

### 3.3 交互类信号

- 用户主动提问。
- 用户追问深度。
- 用户选择讲解风格。
- 用户拒绝或接受推荐。
- 用户对内容点赞或反馈。

### 3.4 环境类信号

- 时间段。
- 剩余开放时间。
- 天气。
- 人流拥挤度。
- 临时活动。
- 设备状态。

## 4. 用户状态标签

建议初期使用可解释标签，而不是直接依赖黑盒评分。

### 4.1 访问阶段

- `entered`：刚进入。
- `orienting`：正在找方向。
- `exploring`：自由探索。
- `deep_viewing`：深度观看。
- `tasking`：正在完成任务。
- `shopping`：接近文创或商品场景。
- `leaving`：准备离开。

### 4.2 兴趣状态

- `low_interest`：快速经过或多次跳过。
- `emerging_interest`：开始停留或点击。
- `strong_interest`：长时间停留、追问、收藏。
- `topic_shift`：兴趣主题发生转移。

### 4.3 服务需求状态

- `needs_orientation`：需要方向或路线。
- `needs_explanation`：适合讲解。
- `needs_recommendation`：适合推荐下一站。
- `needs_interaction`：适合任务或问答。
- `needs_rest`：可能需要休息。
- `needs_commerce`：适合文创推荐。

## 5. Memory 写入原则

### 5.1 区分事实与推断

事实：

- 用户收藏了某展品。
- 用户完成了某任务。
- 用户选择了亲子路线。

推断：

- 用户可能喜欢建筑主题。
- 用户可能偏好短讲解。
- 用户可能对文创感兴趣。

推断需要置信度，不应作为永久事实写死。

### 5.2 控制写入频率

不要把每一次点击都写入长期 Memory。只有当行为重复出现或用户明确表达时，才提升长期偏好权重。

### 5.3 支持衰减和修正

用户兴趣会变化。长期 Memory 应支持：

- 时间衰减。
- 新行为覆盖旧判断。
- 用户主动修改偏好。
- 临时场景偏好不污染长期画像。

## 6. 偏好更新示例

### 6.1 用户多次停留在建筑类展品

```text
事件：用户在 3 个建筑主题点位均停留超过平均值。
判断：architecture 兴趣提升。
动作：提高 architecture 权重，后续路线优先推荐建筑主题。
```

### 6.2 用户跳过长讲解

```text
事件：用户连续 2 次在长讲解开始后快速退出。
判断：当前会话中不适合长内容。
动作：Session Memory 中将 preferred_length 调整为 short。
```

### 6.3 用户主动购买或收藏文创

```text
事件：用户收藏某主题文创商品。
判断：对该主题商品有潜在兴趣。
动作：Commerce preference 中提升对应品类权重。
```

## 7. 隐私与用户控制

用户需要知道系统记录了什么，并能控制记忆。

建议提供：

- 关闭个性化。
- 清除本次访问记录。
- 删除长期画像。
- 查看“我为什么收到这个推荐”。
- 明确授权位置与行为数据。
