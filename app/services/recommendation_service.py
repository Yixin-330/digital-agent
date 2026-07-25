from __future__ import annotations

from typing import Dict, List, Optional

from app.models import RecommendationCard, UserProfile
from app.services.venue_data_service import VenueDataService


class RecommendationService:
    def __init__(self, venue_data: VenueDataService | None = None) -> None:
        self.venue_data = venue_data or VenueDataService()

    def recommend(
        self,
        profile: UserProfile,
        location: Optional[str],
        weather: Optional[str],
        strategy_arm: str = "family_route",
        graph_features: Optional[Dict[str, object]] = None,
        venue_id: Optional[str] = None,
        message: str = "",
    ) -> List[str]:
        resolved_venue_id = self.venue_data.infer_venue_id(venue_id, location, message)
        if resolved_venue_id:
            return self._recommend_for_venue(
                resolved_venue_id,
                profile=profile,
                location=location,
                weather=weather,
                strategy_arm=strategy_arm,
                graph_features=graph_features,
            )

        items: List[str] = []
        interest = profile.preferences.get("interest", "")

        if interest == "history":
            items.append("推荐: 历史文化线路（古城墙 -> 博物馆 -> 非遗工坊）")
        if interest == "food":
            items.append("推荐: 本地美食地图（早茶街 -> 老字号午餐 -> 夜市小吃）")
        if profile.travel_style == "slow":
            items.append("推荐: 慢节奏漫游（公园散步 + 江边咖啡 + 夜间演艺）")
        if profile.travel_style == "intensive":
            items.append("推荐: 一日高密度打卡（3景点 + 1演出 + 1夜游）")
        if weather and ("雨" in weather or "storm" in weather.lower()):
            items.append("提醒: 雨天优先室内场馆（博物馆/美术馆/剧场）")
        if location:
            items.append(f"就近服务: 你当前在 {location}，可优先体验周边 3 公里热门点位。")
        if profile.budget_level == "low":
            items.append("预算友好: 推荐联票与公共交通组合方案。")
        if profile.budget_level == "high":
            items.append("品质优选: 推荐精品酒店 + 私享讲解服务。")
        arm_templates = {
            "culture_route": "主动推荐: 文博深度线（馆藏讲解 + 非遗工坊 + 文化夜游）",
            "food_route": "主动推荐: 在地寻味线（早茶 + 老字号 + 夜市）",
            "family_route": "主动推荐: 亲子友好线（互动展 + 轻徒步 + 早归）",
            "rainyday_indoor": "主动推荐: 雨天室内线（博物馆 + 美术馆 + 茶空间）",
            "night_show": "主动推荐: 夜间演艺线（灯光秀 + 沉浸演出）",
        }
        items.insert(0, arm_templates.get(strategy_arm, arm_templates["family_route"]))
        if graph_features:
            topic_hint = graph_features.get("short_term_topics", [])
            if topic_hint:
                items.append(f"兴趣图谱提示: 近期偏好主题 {topic_hint}")
        return items[:6] if items else ["推荐: 城市经典一日游（地标景点 + 在地美食 + 夜游演出）"]

    def recommend_cards(
        self,
        profile: UserProfile,
        location: Optional[str],
        weather: Optional[str],
        strategy_arm: str = "family_route",
        graph_features: Optional[Dict[str, object]] = None,
        venue_id: Optional[str] = None,
        message: str = "",
    ) -> List[RecommendationCard]:
        resolved_venue_id = self.venue_data.infer_venue_id(venue_id, location, message)
        if resolved_venue_id:
            return self._recommend_cards_for_venue(
                resolved_venue_id,
                profile=profile,
                location=location,
                weather=weather,
                strategy_arm=strategy_arm,
                graph_features=graph_features,
            )
        legacy_items = self.recommend(profile, location, weather, strategy_arm, graph_features, venue_id, message)
        return [
            RecommendationCard(
                id=f"legacy_{index}",
                type="suggestion",
                title=item.split(":", 1)[0] if ":" in item else "推荐",
                description=item.split(":", 1)[1].strip() if ":" in item else item,
                reason="根据当前对话、画像和基础推荐策略生成。",
                action_label="查看建议",
                priority=max(0.2, 0.75 - index * 0.08),
            )
            for index, item in enumerate(legacy_items)
        ]

    def _recommend_for_venue(
        self,
        venue_id: str,
        profile: UserProfile,
        location: Optional[str],
        weather: Optional[str],
        strategy_arm: str,
        graph_features: Optional[Dict[str, object]],
    ) -> List[str]:
        routes = self.venue_data.list_routes(venue_id)
        spots = self.venue_data.list_spots(venue_id)
        tasks = self.venue_data.list_tasks(venue_id)
        products = self.venue_data.list_products(venue_id)
        items: List[str] = []

        route = self._select_route(routes, profile, strategy_arm, weather)
        if route:
            sequence = " -> ".join(self._spot_name(spots, str(spot_id)) for spot_id in route.get("spot_sequence", []))
            venue_name = self.venue_data.venue_name(venue_id)
            items.append(f"{venue_name}路线: {route['name']}（约 {route['duration_minutes']} 分钟）: {sequence}")
            items.append(f"推荐理由: {route['recommendation_reason']}")

        spot = self._select_spot(spots, profile, location)
        if spot:
            items.append(f"重点点位: {spot['name']} - {spot['summary']}")

        task = self._select_task(tasks, profile, str(spot.get("id")) if spot else None)
        if task:
            items.append(f"互动任务: {task['name']} - {task['description']}")

        product = self._select_product(products, profile)
        if product:
            items.append(f"文创推荐: {product['name']} - {product['cultural_link']}")

        if weather and "雨" in weather:
            items.append("天气提醒: 雨天建议优先选择华严寺、剪纸体验点等室内或半室内内容，并以现场开放情况为准。")
        if graph_features and graph_features.get("short_term_topics"):
            items.append(f"兴趣图谱提示: 近期偏好主题 {graph_features['short_term_topics']}")
        return items[:6]

    def _recommend_cards_for_venue(
        self,
        venue_id: str,
        profile: UserProfile,
        location: Optional[str],
        weather: Optional[str],
        strategy_arm: str,
        graph_features: Optional[Dict[str, object]],
    ) -> List[RecommendationCard]:
        routes = self.venue_data.list_routes(venue_id)
        spots = self.venue_data.list_spots(venue_id)
        tasks = self.venue_data.list_tasks(venue_id)
        products = self.venue_data.list_products(venue_id)
        cards: List[RecommendationCard] = []

        route = self._select_route(routes, profile, strategy_arm, weather)
        if route:
            sequence = [self._spot_name(spots, str(spot_id)) for spot_id in route.get("spot_sequence", [])]
            cards.append(
                RecommendationCard(
                    id=str(route.get("id", "route")),
                    type="route",
                    title=str(route.get("name", "推荐路线")),
                    subtitle=f"约 {route.get('duration_minutes', '?')} 分钟",
                    description=" -> ".join(sequence),
                    reason=str(route.get("recommendation_reason", "")),
                    action_label="查看路线",
                    priority=0.92,
                    tags=[str(item) for item in route.get("target_users", [])],
                    metadata={
                        "venue_id": venue_id,
                        "spot_sequence": [str(item) for item in route.get("spot_sequence", [])],
                        "duration_minutes": int(route.get("duration_minutes", 0) or 0),
                    },
                )
            )

        spot = self._select_spot(spots, profile, location)
        if spot:
            cards.append(
                RecommendationCard(
                    id=str(spot.get("id", "spot")),
                    type="spot",
                    title=str(spot.get("name", "重点点位")),
                    subtitle=str(spot.get("type", "文化点位")),
                    description=str(spot.get("summary", "")),
                    reason="适合你当前的位置、兴趣或同行状态。",
                    action_label="听讲解",
                    priority=0.82,
                    tags=[str(item) for item in spot.get("tags", [])[:5]],
                    metadata={
                        "venue_id": venue_id,
                        "recommended_duration_minutes": int(spot.get("recommended_duration_minutes", 0) or 0),
                    },
                )
            )

        task = self._select_task(tasks, profile, str(spot.get("id")) if spot else None)
        if task:
            cards.append(
                RecommendationCard(
                    id=str(task.get("id", "task")),
                    type="task",
                    title=str(task.get("name", "互动任务")),
                    subtitle=str(task.get("type", "轻互动")),
                    description=str(task.get("description", "")),
                    reason="用轻任务把文化内容变成可参与体验。",
                    action_label="开始任务",
                    priority=0.74,
                    tags=[str(item) for item in task.get("target_users", [])],
                    metadata={
                        "venue_id": venue_id,
                        "trigger_spots": [str(item) for item in task.get("trigger_spots", [])],
                        "memory_signal": task.get("memory_signal", {}),
                    },
                )
            )

        product = self._select_product(products, profile)
        if product:
            cards.append(
                RecommendationCard(
                    id=str(product.get("id", "product")),
                    type="product",
                    title=str(product.get("name", "文创推荐")),
                    subtitle=str(product.get("category", "文创")),
                    description=str(product.get("cultural_link", "")),
                    reason=str(product.get("recommendation_style", "与当前文化兴趣相关，适合收藏或稍后查看。")),
                    action_label="收藏看看",
                    priority=0.58,
                    tags=[str(item) for item in product.get("recommend_to", [])],
                    metadata={
                        "venue_id": venue_id,
                        "requires_verification": product.get("requires_verification", []),
                    },
                )
            )

        if weather and "雨" in weather:
            cards.append(
                RecommendationCard(
                    id="weather_rain_hint",
                    type="reminder",
                    title="雨天路线提醒",
                    subtitle="体验调整",
                    description="雨天建议优先选择华严寺、剪纸体验点等室内或半室内内容，并以现场开放情况为准。",
                    reason="根据当前天气状态降低户外停留风险。",
                    action_label="调整路线",
                    priority=0.7,
                    tags=["weather", "route_adjustment"],
                    metadata={"venue_id": venue_id},
                )
            )
        if graph_features and graph_features.get("short_term_topics"):
            cards.append(
                RecommendationCard(
                    id="interest_graph_hint",
                    type="memory_hint",
                    title="近期兴趣提示",
                    subtitle="本次会话",
                    description=f"近期偏好主题：{graph_features['short_term_topics']}",
                    reason="由本次会话中的兴趣图谱沉淀生成。",
                    action_label="继续沿这个方向",
                    priority=0.45,
                    tags=[str(item) for item in graph_features.get("short_term_topics", [])],
                    metadata={"venue_id": venue_id},
                )
            )
        return cards[:6]

    def _select_route(
        self,
        routes: List[Dict[str, object]],
        profile: UserProfile,
        strategy_arm: str,
        weather: Optional[str],
    ) -> Optional[Dict[str, object]]:
        if not routes:
            return None
        if strategy_arm == "night_show":
            return self._first_route(routes, "night_tour")
        if profile.preferences.get("group_type") == "family":
            return self._first_route(routes, "family")
        if profile.preferences.get("interest") == "history":
            return self._first_route(routes, "culture_deep")
        if weather and "雨" in weather:
            return self._first_route(routes, "culture_deep")
        return self._first_route(routes, "first_time_visitor") or routes[0]

    def _first_route(self, routes: List[Dict[str, object]], target_user: str) -> Optional[Dict[str, object]]:
        for route in routes:
            if target_user in route.get("target_users", []):
                return route
        return None

    def _select_spot(
        self,
        spots: List[Dict[str, object]],
        profile: UserProfile,
        location: Optional[str],
    ) -> Optional[Dict[str, object]]:
        if not spots:
            return None
        text = location or ""
        for spot in spots:
            if str(spot.get("name", "")) in text:
                return spot
        preferred_tags: List[str] = []
        if profile.preferences.get("interest") == "history":
            preferred_tags.extend(["古堡", "古建筑", "全国重点文物保护单位"])
        if profile.preferences.get("group_type") == "family":
            preferred_tags.extend(["亲子互动", "研学", "文创", "非遗"])
        for spot in spots:
            tags = set(spot.get("tags", []))
            if any(tag in tags for tag in preferred_tags):
                return spot
        return spots[0]

    def _select_task(
        self,
        tasks: List[Dict[str, object]],
        profile: UserProfile,
        spot_id: Optional[str],
    ) -> Optional[Dict[str, object]]:
        if not tasks:
            return None
        if spot_id:
            for task in tasks:
                if spot_id in task.get("trigger_spots", []):
                    return task
        if profile.preferences.get("group_type") == "family":
            for task in tasks:
                if "family" in task.get("target_users", []):
                    return task
        return tasks[0]

    def _select_product(
        self,
        products: List[Dict[str, object]],
        profile: UserProfile,
    ) -> Optional[Dict[str, object]]:
        if not products:
            return None
        if profile.budget_level == "low":
            for product in products:
                if "budget_low" in product.get("recommend_to", []):
                    return product
        if profile.preferences.get("group_type") == "family":
            for product in products:
                if "family" in product.get("recommend_to", []):
                    return product
        return products[0]

    def _spot_name(self, spots: List[Dict[str, object]], spot_id: str) -> str:
        for spot in spots:
            if spot.get("id") == spot_id:
                return str(spot.get("name", spot_id))
        return spot_id

