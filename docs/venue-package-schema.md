# 场景包 Schema 说明：Venue Package v0.1

本文档用于固化当前项目中的“场馆 / 景区场景包”数据格式。现阶段它是一个 JSON 场景包，而不是数据库表结构。

当前暖泉古镇场景包文件：

```text
app/data/venues/nuanquan_ancient_town.json
```

后续新增景区时，优先复制该文件结构，替换为新的 `venue_id` 与对应知识、路线、任务、文创、触发规则。

## 1. 顶层结构

当前固化的 v0.1 结构如下：

```json
{
  "venue": {},
  "sources": [],
  "spots": [],
  "routes": [],
  "tasks": [],
  "products": [],
  "personas": [],
  "context_rules": [],
  "review_needed": []
}
```

其中，真正支撑 Demo 运行的核心字段是：

- `venue`：场景基础信息
- `spots`：点位 / 景点 / 文化节点
- `routes`：游览路线
- `tasks`：互动任务
- `products`：文创 / 消费推荐对象
- `sources`：文化知识依据与人工核验来源

`personas`、`context_rules`、`review_needed` 当前已经进入数据包，但更多承担产品规划、主动服务策略和人工审查辅助作用。

## 2. venue：场景基础信息

```json
{
  "venue": {
    "id": "nuanquan_ancient_town",
    "name": "蔚县暖泉古镇",
    "location": {
      "province": "河北省",
      "city": "张家口市",
      "county": "蔚县",
      "town": "暖泉镇"
    },
    "positioning": "以古堡、民俗、非遗打树花、剪纸与古镇游线为核心的文化体验场景",
    "demo_scope": "用于概念验证 Demo 的 P0 场景包",
    "data_status": "draft_for_review"
  }
}
```

当前代码依赖：

- `venue.id`：场景包唯一标识，用于路由和推荐识别
- `venue.name`：前端展示、推荐文案、Graph RAG 回答引用
- `venue.location`：用于根据用户位置或输入文本推断当前场景

建议 v0.2 补充：

- `schema_version`
- `package_version`
- `aliases`
- `venue_type`
- `geo_center`
- `updated_at`
- `owner`

## 3. sources：知识来源

```json
{
  "id": "source_official_001",
  "title": "资料来源标题",
  "url": "https://example.com",
  "notes": "来源说明或人工核验备注"
}
```

用途：

- 给 Graph RAG 回答提供可追溯依据
- 标记哪些知识来自公开资料、人工整理或待核验材料
- 后续合作上线时支撑内容版权、可信度和审查流程

## 4. spots：点位知识节点

```json
{
  "id": "west_ancient_fort",
  "name": "西古堡",
  "type": "古堡 / 古建 / 非遗场景 / 民俗点位",
  "area": "暖泉古镇核心区",
  "summary": "面向推荐和卡片展示的短摘要",
  "story": "面向数字人讲解的文化故事正文",
  "tags": ["古堡", "明清建筑", "历史文化"],
  "suitable_for": ["亲子家庭", "历史文化兴趣用户"],
  "recommended_duration_minutes": 35,
  "trigger_services": ["文化讲解", "拍照建议", "路线续航"],
  "related_tasks": ["fort_discovery_task"],
  "related_products": ["paper_cutting_souvenir"],
  "evidence": ["source_official_001"],
  "confidence": "medium",
  "requires_verification": true
}
```

当前代码依赖：

- `id`：Graph RAG 建图、任务 / 文创关联
- `name`：点位识别、展示和文化问答
- `summary`：推荐文案
- `story`：文化讲解内容
- `tags`：主题归类、Graph RAG 主题节点生成
- `related_tasks`：点位到互动任务的图谱关系
- `related_products`：点位到文创推荐的图谱关系
- `evidence`：知识来源引用

## 5. routes：路线推荐

```json
{
  "id": "family_light_route",
  "name": "亲子轻量文化路线",
  "target_users": ["亲子家庭", "首次到访用户"],
  "duration_minutes": 90,
  "spot_sequence": ["west_ancient_fort", "paper_cutting_area", "dashuhua_show_area"],
  "recommendation_reason": "适合第一次到访，节奏轻，不需要长时间步行",
  "context_triggers": {
    "group_type": "family",
    "stay_time_minutes": "60-120",
    "interest": ["民俗", "非遗", "亲子"]
  },
  "requires_verification": true
}
```

当前代码依赖：

- `name`
- `duration_minutes`
- `spot_sequence`
- `recommendation_reason`
- `target_users`

用途：

- 根据用户状态、兴趣、同行人群和停留时长进行路线推荐
- 给可控主动决策引擎提供可执行候选动作

## 6. tasks：互动任务

```json
{
  "id": "paper_cutting_find_task",
  "name": "寻找剪纸纹样任务",
  "type": "互动探索",
  "trigger_spots": ["paper_cutting_area"],
  "description": "引导用户观察剪纸纹样并完成轻互动",
  "target_users": ["亲子家庭", "非遗兴趣用户"],
  "memory_signal": "用户对非遗手作表现出兴趣"
}
```

当前代码依赖：

- `name`
- `description`
- `trigger_spots`
- `target_users`

用途：

- 作为主动服务的轻任务
- 通过 `memory_signal` 沉淀用户偏好，后续进入短期记忆或长期画像

## 7. products：文创 / 消费推荐

```json
{
  "id": "paper_cutting_souvenir",
  "name": "蔚县剪纸文创",
  "category": "非遗文创",
  "cultural_link": "与蔚县剪纸非遗文化相关",
  "recommend_to": ["非遗兴趣用户", "亲子家庭"],
  "recommendation_style": "文化解释优先，避免强推销",
  "requires_verification": true
}
```

当前代码依赖：

- `name`
- `cultural_link`
- `recommend_to`

用途：

- 支撑文化内容到消费推荐的连接
- 后续可迁移到电商推荐、消费服务和本地生活场景

## 8. personas：Demo 用户画像

```json
{
  "id": "family_first_visit",
  "name": "首次到访的亲子家庭",
  "goals": ["轻松游览", "孩子能参与", "理解本地文化"],
  "preferred_services": ["轻量路线", "互动任务", "非遗讲解"]
}
```

当前用途：

- Demo 剧本
- 前端场景切换
- 推荐逻辑演示

注意：这不是长期用户记忆本体，只是用于演示的典型用户模板。

## 9. context_rules：主动服务触发规则

```json
{
  "id": "long_stay_near_fort",
  "trigger": {
    "location": "west_ancient_fort",
    "stay_minutes_gte": 8,
    "interest": ["历史", "古建"]
  },
  "action": "主动触发西古堡文化讲解",
  "candidate_routes": ["history_deep_route"],
  "cooldown_minutes": 20,
  "policy": "只提示一次，用户拒绝后不重复打扰",
  "requires_verification": true
}
```

当前用途：

- 表达主动服务策略
- 给后续“可控主动决策引擎”提供规则基础

注意：当前 Demo 还没有完整执行规则引擎，`context_rules` 更接近策略数据草案。

## 10. review_needed：人工审查清单

```json
[
  "西古堡开放时间需要人工核验",
  "打树花演出时间需要核验",
  "文创商品名称与售卖点需要合作方确认"
]
```

用途：

- 标记 P0 阶段不能直接用于上线的内容
- 方便你后续审查和补充真实合作数据

## 11. 当前 Graph RAG 映射关系

当前系统会把场景包转成图知识结构：

| JSON 字段 | 图谱含义 |
| --- | --- |
| `venue` | 场景根节点 |
| `spots` | 文化点位节点 |
| `spot.tags` | 主题节点 |
| `tasks` | 互动任务节点 |
| `products` | 文创 / 消费节点 |
| `spot.related_tasks` | 点位触发任务关系 |
| `spot.related_products` | 点位关联文创关系 |
| `spot.evidence` | 回答引用来源 |

因此，当前场景包既是推荐数据，也是 Graph RAG 文化讲解知识源。

## 12. 当前边界

当前 v0.1 已足够支撑暖泉古镇 Demo：

- 能识别暖泉场景
- 能输出路线推荐
- 能围绕点位生成文化讲解
- 能触发任务与文创推荐
- 能保留来源和待核验标记

但它还不是完整上线级 Schema，主要缺口是：

- 缺少严格 JSON Schema 自动校验
- 缺少统一版本号与变更记录
- 缺少开放时间、票务、坐标、地图、无障碍、风险提示等运营字段
- 缺少多语言内容结构
- 缺少媒体资产结构，例如图片、音频、视频、3D 模型
- 缺少内容审核状态与发布状态

## 13. 建议 v0.2 固化方向

建议下一版升级为：

```json
{
  "schema_version": "venue_package.v0.2",
  "package_version": "2026.07.23-draft",
  "venue": {},
  "operations": {},
  "sources": [],
  "spots": [],
  "routes": [],
  "tasks": [],
  "products": [],
  "context_rules": [],
  "personas": [],
  "media_assets": [],
  "review_needed": []
}
```

v0.2 的重点不是推翻当前结构，而是在当前结构上补齐可迁移、可校验、可上线的字段。
