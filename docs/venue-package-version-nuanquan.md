# 暖泉古镇场景包版本设计

## 1. 版本定位

当前版本建议定义为：

> 用户关系智能体底座的第一个场景包版本：`nuanquan_ancient_town`

也就是说，暖泉古镇不是一套独立写死的产品逻辑，而是运行在通用数字底座之上的一个行业/景区数据包。

底层通用能力保持不变：

- Context 感知。
- Memory 沉淀。
- Graph RAG 讲解。
- 推荐与决策。
- Tool Calling。
- Workflow 编排。
- Trust 与安全控制。
- 前端 Demo 展示框架。

需要随景区替换的是：

- 景区基础信息。
- 点位。
- 路线。
- 互动任务。
- 文创商品。
- 文化知识来源。
- 图谱节点与关系。
- 运营规则。
- 服务设施和动态信息。

## 2. 当前工程形态

当前已将暖泉数据放入：

```text
app/data/venues/nuanquan_ancient_town.json
```

该文件作为暖泉古镇场景包的数据种子。

旧文件仍保留：

```text
app/data/nuanquan_demo_data.json
```

主要用于历史文档引用和兼容，不再作为长期主路径。

## 3. 场景包目录约定

后续每个景区或行业场景都可以新增一个 JSON：

```text
app/data/venues/{venue_id}.json
```

示例：

```text
app/data/venues/nuanquan_ancient_town.json
app/data/venues/example_museum.json
app/data/venues/example_commercial_street.json
```

系统启动时会扫描 `app/data/venues/*.json`，自动加载可用场景。

## 4. 场景包数据结构

一个完整场景包建议包含：

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

其中：

- `venue`：场景基础信息和别名。
- `sources`：知识来源。
- `spots`：点位。
- `routes`：路线。
- `tasks`：互动任务。
- `products`：文创或商品。
- `personas`：典型用户类型。
- `context_rules`：场景触发规则。
- `review_needed`：需人工核验的信息。

## 5. 通用能力如何复用

### 5.1 场景识别

`VenueDataService` 会根据以下信息推断场景：

- 显式传入的 `venue_id`。
- `venue.name`。
- `venue.aliases`。
- `venue.location`。
- 点位名称。
- 路线名称。

因此后续接入新景区时，不需要改上层代码，只需要在新场景包里补充名称和别名。

### 5.2 推荐服务

推荐服务会读取当前场景包中的：

- `routes`
- `spots`
- `tasks`
- `products`

再结合用户画像和上下文输出：

- 路线推荐。
- 重点点位。
- 互动任务。
- 文创推荐。

暖泉版本当前可展示：

- 初次到访路线。
- 古建与文化深度路线。
- 亲子非遗互动路线。
- 夜游打树花路线。
- 西古堡、剪纸、打树花相关任务和文创。

### 5.3 Graph RAG

`CultureKGService` 会从所有场景包动态构建知识图谱：

- 场景转为场景节点。
- 点位转为点位节点。
- 任务转为互动任务节点。
- 文创转为商品节点。
- 点位与任务、文创、主题之间生成关系边。
- `sources/evidence` 转为证据来源。

因此换景区时，不需要重写 Graph RAG 逻辑。

### 5.4 前端 Demo

当前 `frontend-demo` 是暖泉演示界面，仍有暖泉文案和点位。

短期建议：

- 保留暖泉作为第一个可演示版本。

中期建议：

- 将前端场景配置也从 JSON 读取。
- 支持 `?venue_id=xxx` 切换场景。
- 将按钮、地图点位、演示脚本改为配置驱动。

## 6. 暖泉古镇版本目前能证明什么

暖泉版本可以证明：

1. 通用数字底座可以加载一个具体景区的数据包。
2. 上层能力不需要为每个景区重写。
3. 路线、讲解、任务、文创推荐可以由场景包驱动。
4. Graph RAG 可以从场景数据动态构建知识图谱。
5. 后续复制到其他景区时，核心工作是数据接入和内容审核。

## 7. 后续复制到新景区的步骤

复制流程：

```text
1. 新建 app/data/venues/{new_venue_id}.json
2. 填写 venue 基础信息和 aliases
3. 填写 spots 点位
4. 填写 routes 路线
5. 填写 tasks 互动任务
6. 填写 products 商品或服务
7. 填写 sources/evidence 知识来源
8. 启动服务
9. 通过 venue_id 调用 /chat 或 /recommendations
10. 前端切换到对应场景配置
```

不需要重写：

- Agent Orchestrator。
- Memory Service。
- Recommendation Service 主逻辑。
- Graph RAG 构图逻辑。
- Workflow 框架。
- Trust/Safety 框架。

## 8. 下一步建议

为了把“暖泉版本”打磨成可复用模板，建议下一步做：

1. 给 `venue` 增加 `aliases` 字段，提升场景识别能力。
2. 把推荐返回从字符串升级为结构化卡片。
3. 把前端 Demo 的场景按钮和点位图配置化。
4. 增加 `/api/v1/venues` 接口，列出已加载场景包。
5. 增加场景包 schema 校验，避免数据格式错误。
6. 编写 `docs/venue-package-schema.md`，作为后续接入新景区的数据模板。

## 9. 结论

当前完全可以基于暖泉古镇开发出一个版本。

这个版本的正确定位是：

> 暖泉古镇不是上层能力的特例，而是通用数字底座上的第一个可插拔场景包。

后续更换景区时，重点替换和补充的是场景知识、路线、任务、商品和运营数据，而不是重做数字人的上层能力。
