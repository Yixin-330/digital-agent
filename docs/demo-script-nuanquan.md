# 暖泉古镇情境感知数字人概念验证 Demo 脚本

## 1. Demo 目标

本 Demo 用于验证“多模态情境感知数字人”的核心产品机制是否成立。

重点不是证明数据已经完整上线，而是证明系统可以基于当前场景、用户状态和长期偏好，完成以下闭环：

1. 识别用户所在文化场景。
2. 根据用户状态推荐路线。
3. 基于 Graph RAG 给出可信文化讲解。
4. 主动触发互动任务。
5. 将文化兴趣自然连接到文创和消费服务。
6. 将用户行为沉淀为后续 Memory 信号。

## 2. Demo 场景设定

场景：河北蔚县暖泉古镇  
用户：第一次到访的亲子家庭  
时间：下午，还有约 2 小时  
兴趣：希望轻松游览，了解西古堡、蔚县剪纸，晚上可能看打树花  
系统身份：暖泉古镇情境感知数字人

## 3. 演示前准备

### 3.1 启动服务

```powershell
C:\Users\Lenovo\.venvs\wenlv-agent\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3.2 健康检查

```powershell
curl http://127.0.0.1:8000/health
```

预期返回：

```json
{"status": "ok"}
```

### 3.3 运行测试

```powershell
C:\Users\Lenovo\.venvs\wenlv-agent\Scripts\python.exe -m pytest -q
```

预期结果：

```text
6 passed
```

## 4. Demo 主线

### Step 1：用户进入暖泉古镇

用户输入：

```text
我第一次来暖泉古镇，带孩子，下午还有两个小时，怎么逛比较合适？
```

API 示例：

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d "{\"user_id\":\"demo_family_001\",\"session_id\":\"demo_session_001\",\"venue_id\":\"nuanquan_ancient_town\",\"message\":\"我第一次来暖泉古镇，带孩子，下午还有两个小时，怎么逛比较合适？\",\"location\":\"暖泉古镇入口\"}"
```

系统应展示：

- 识别为暖泉古镇场景。
- 识别用户为亲子家庭。
- 推荐亲子或初次到访路线。
- 返回路线包含西古堡、古街巷、蔚县剪纸体验点等。

演示讲解重点：

> 系统不是只回答“怎么玩”，而是结合场景、同行人群和剩余时间生成路线建议。

## 5. Step 2：文化点位可信讲解

用户输入：

```text
西古堡有什么特别？
```

API 示例：

```powershell
curl "http://127.0.0.1:8000/api/v1/knowledge/grounded-answer?query=请介绍暖泉古镇的西古堡"
```

系统应展示：

- Graph RAG 从暖泉知识图谱检索西古堡。
- 返回西古堡摘要。
- 返回证据来源。
- 不再出现青铜鼓、皮影戏等通用样例。

演示讲解重点：

> 文化讲解不是模型自由发挥，而是先从暖泉知识图谱中检索，再生成可追溯回答。

## 6. Step 3：主动触发互动任务

系统可主动推荐：

```text
你可以带孩子做一个“寻找古堡细节”的小任务：在古堡或街巷中寻找一个门楼、砖雕、窗格或院落细节，然后告诉我你看到了什么。
```

可演示的系统输出来自推荐结果中的：

- `互动任务: 寻找古堡细节`
- `互动任务: 识别剪纸纹样`

演示讲解重点：

> 数字人不是只讲解，而是能把用户从“听”引导到“参与”，提升沉浸感和停留时长。

## 7. Step 4：兴趣变化与路线调整

用户输入：

```text
孩子对剪纸挺感兴趣，我们想多看看非遗相关的内容。
```

API 示例：

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d "{\"user_id\":\"demo_family_001\",\"session_id\":\"demo_session_001\",\"venue_id\":\"nuanquan_ancient_town\",\"message\":\"孩子对剪纸挺感兴趣，我们想多看看非遗相关的内容。\",\"location\":\"蔚县剪纸体验点\"}"
```

系统应展示：

- 推荐蔚县剪纸体验点。
- 推荐识别剪纸纹样任务。
- 推荐剪纸相关文创。

演示讲解重点：

> 用户表达兴趣后，系统会把“剪纸”作为新的偏好信号，影响后续任务和消费推荐。

## 8. Step 5：夜游打树花意图

用户输入：

```text
晚上想看打树花，应该怎么安排？
```

API 示例：

```powershell
curl -X POST http://127.0.0.1:8000/api/v1/chat `
  -H "Content-Type: application/json" `
  -d "{\"user_id\":\"demo_family_001\",\"session_id\":\"demo_session_001\",\"venue_id\":\"nuanquan_ancient_town\",\"message\":\"晚上想看打树花，应该怎么安排？\",\"location\":\"暖泉古镇\"}"
```

系统应展示：

- 推荐夜游打树花路线。
- 提醒打树花演出时间、票价和预约方式属于动态信息，需要以现场或官方信息为准。
- 可推荐打树花主题记忆任务或纪念品。

演示讲解重点：

> Context 不只包含位置，也包含时间、活动和用户意图。系统可以从白天游览切换到夜游场景。

## 9. Step 6：文化兴趣到文创推荐

用户输入：

```text
有什么适合带走的纪念品？
```

API 示例：

```powershell
curl -X GET "http://127.0.0.1:8000/api/v1/users/demo_family_001/recommendations?venue_id=nuanquan_ancient_town&location=蔚县剪纸体验点"
```

系统应展示：

- 蔚县剪纸作品。
- 剪纸纹样书签或小卡。
- 打树花主题冰箱贴或纪念章。
- 说明推荐理由与文化关联。

演示讲解重点：

> 文创推荐不是硬广告，而是基于用户已经表现出的文化兴趣、游览阶段和场景关系给出可信推荐。

## 10. 推荐演示顺序

建议实际演示时按以下顺序：

1. `/health` 健康检查。
2. `/api/v1/chat` 展示暖泉路线推荐。
3. `/api/v1/knowledge/grounded-answer` 展示 Graph RAG 文化讲解。
4. `/api/v1/chat` 展示亲子/剪纸兴趣变化。
5. `/api/v1/chat` 展示夜游打树花意图。
6. `/api/v1/users/{user_id}/recommendations` 展示文创推荐。

## 11. Demo 成功标准

本阶段 Demo 成功，不要求数据完整上线，只要求证明以下能力：

- 用户说暖泉相关内容时，系统能进入暖泉场景。
- 推荐结果来自暖泉数据，而不是通用文旅模板。
- 文化讲解来自暖泉知识图谱，并带证据来源。
- 系统可以同时返回路线、点位、任务和文创推荐。
- 动态运营信息能明确提示“需现场或官方确认”。

## 12. 当前限制

当前 Demo 暂不承诺：

- 真实地图导航。
- 实时定位。
- 实时演出时间。
- 实时票价和预约。
- 真实商户库存。
- 上线级文化资料审核。

这些限制不影响概念验证，但在合作试点前需要补齐。
