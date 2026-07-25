from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Set


class CultureKGService:
    def __init__(self) -> None:
        data_dir = Path(__file__).resolve().parent.parent / "data"
        venue_dir = data_dir / "venues"
        graphs = []
        if venue_dir.exists():
            for venue_path in sorted(venue_dir.glob("*.json")):
                graphs.append(self._build_graph_from_venue(json.loads(venue_path.read_text(encoding="utf-8"))))
        if graphs:
            self.graph = self._merge_graphs(graphs)
        else:
            path = data_dir / "culture_kg.json"
            self.graph = json.loads(path.read_text(encoding="utf-8"))

    def query_subgraph(self, query: str) -> Dict[str, object]:
        nodes = self.graph.get("nodes", [])
        edges = self.graph.get("edges", [])
        evidence = self.graph.get("evidence", {})
        query_text = query.lower()
        matched_nodes = [node for node in nodes if self._node_matches(node, query_text)]
        if not matched_nodes:
            return {"nodes": [], "edges": [], "citations": []}
        matched_ids = {node["id"] for node in matched_nodes}
        expansion_seeds = {node["id"] for node in matched_nodes if node.get("type") != "场景"} or matched_ids
        expanded_ids = self._expand_related_ids(expansion_seeds, edges)
        selected_ids = matched_ids | expanded_ids
        related_nodes = [node for node in nodes if node["id"] in selected_ids and node["id"] not in matched_ids]
        selected_nodes = matched_nodes + related_nodes
        matched_edges = [edge for edge in edges if edge["source"] in selected_ids and edge["target"] in selected_ids]
        citations: List[Dict[str, str]] = []
        for node in selected_nodes:
            for ev in evidence.get(node["id"], [])[:2]:
                citations.append(
                    {
                        "node": str(node["name"]),
                        "node_id": str(node["id"]),
                        "source": ev,
                        "source_type": self._source_type(ev),
                        "confidence": self._evidence_confidence(ev),
                    }
                )
        return {"nodes": selected_nodes[:6], "edges": matched_edges[:10], "citations": citations[:6]}

    def _node_matches(self, node: Dict[str, object], query_text: str) -> bool:
        fields: List[str] = [str(node.get("name", "")), str(node.get("type", "")), str(node.get("summary", ""))]
        fields.extend(str(tag) for tag in node.get("tags", []))
        fields.extend(str(alias) for alias in node.get("aliases", []))
        return any(field and field.lower() in query_text for field in fields)

    def _expand_related_ids(self, matched_ids: Set[str], edges: List[Dict[str, str]]) -> Set[str]:
        expanded = set(matched_ids)
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            if source in matched_ids:
                expanded.add(target)
            if target in matched_ids:
                expanded.add(source)
        return expanded

    def _build_graph_from_venue(self, data: Dict[str, object]) -> Dict[str, object]:
        sources_by_id = {source["id"]: source for source in data.get("sources", [])}
        nodes: List[Dict[str, object]] = []
        edges: List[Dict[str, str]] = []
        evidence: Dict[str, List[str]] = {}
        venue = data.get("venue", {})
        venue_id = str(venue.get("id", "venue"))
        nodes.append(
            {
                "id": venue_id,
                "name": str(venue.get("name", "场馆")),
                "type": "场景",
                "summary": str(venue.get("positioning", "")),
                "tags": self._venue_tokens(venue),
                "aliases": self._venue_aliases(venue),
            }
        )
        evidence[venue_id] = [str(venue.get("demo_scope", "P0 场景数据草案"))]

        for spot in data.get("spots", []):
            node_id = str(spot["id"])
            nodes.append(
                {
                    "id": node_id,
                    "name": str(spot["name"]),
                    "type": str(spot.get("type", "点位")),
                    "summary": str(spot.get("summary", "")),
                    "tags": list(spot.get("tags", [])),
                    "aliases": [str(spot["name"])],
                }
            )
            edges.append({"source": venue_id, "target": node_id, "relation": "包含点位"})
            evidence[node_id] = self._resolve_evidence(spot.get("evidence", []), sources_by_id)
            for product_id in spot.get("related_products", []):
                edges.append({"source": node_id, "target": str(product_id), "relation": "关联文创"})
            for task_id in spot.get("related_tasks", []):
                edges.append({"source": node_id, "target": str(task_id), "relation": "触发任务"})

        for task in data.get("tasks", []):
            node_id = str(task["id"])
            nodes.append(
                {
                    "id": node_id,
                    "name": str(task["name"]),
                    "type": "互动任务",
                    "summary": str(task.get("description", "")),
                    "tags": list(task.get("target_users", [])),
                    "aliases": [str(task["name"])],
                }
            )
            evidence[node_id] = [str(task.get("description", ""))]
            for spot_id in task.get("trigger_spots", []):
                edges.append({"source": str(spot_id), "target": node_id, "relation": "可触发"})

        for product in data.get("products", []):
            node_id = str(product["id"])
            nodes.append(
                {
                    "id": node_id,
                    "name": str(product["name"]),
                    "type": "文创商品",
                    "summary": str(product.get("cultural_link", "")),
                    "tags": [str(product.get("category", "文创")), *list(product.get("recommend_to", []))],
                    "aliases": [str(product["name"])],
                }
            )
            evidence[node_id] = [str(product.get("cultural_link", "")), str(product.get("recommendation_style", ""))]

        self._add_theme_node(nodes, edges, evidence, "theme_dashuhua", "打树花", "非遗民俗", venue_id)
        self._add_theme_node(nodes, edges, evidence, "theme_papercut", "蔚县剪纸", "国家级非遗", venue_id)
        self._add_theme_node(nodes, edges, evidence, "theme_fortress", "古堡建筑", "古镇空间", venue_id)
        return {"nodes": nodes, "edges": edges, "evidence": evidence}


    def _merge_graphs(self, graphs: List[Dict[str, object]]) -> Dict[str, object]:
        nodes: List[Dict[str, object]] = []
        edges: List[Dict[str, str]] = []
        evidence: Dict[str, List[str]] = {}
        for graph in graphs:
            nodes.extend(graph.get("nodes", []))
            edges.extend(graph.get("edges", []))
            evidence.update(graph.get("evidence", {}))
        return {"nodes": nodes, "edges": edges, "evidence": evidence}

    def _venue_aliases(self, venue: Dict[str, object]) -> List[str]:
        aliases = [str(venue.get("name", ""))]
        aliases.extend(str(alias) for alias in venue.get("aliases", []))
        return [alias for alias in aliases if alias]

    def _venue_tokens(self, venue: Dict[str, object]) -> List[str]:
        tokens = self._venue_aliases(venue)
        location = venue.get("location", {})
        if isinstance(location, dict):
            tokens.extend(str(value) for value in location.values())
        return [token for token in tokens if token]

    def _derive_core_tags(self, data: Dict[str, object]) -> List[str]:
        tags: List[str] = []
        for spot in data.get("spots", []):
            for tag in spot.get("tags", []):
                if str(tag) not in tags:
                    tags.append(str(tag))
        return tags[:3]
    def _resolve_evidence(self, source_ids: object, sources_by_id: Dict[str, Dict[str, str]]) -> List[str]:
        resolved: List[str] = []
        for source_id in source_ids if isinstance(source_ids, list) else []:
            source = sources_by_id.get(str(source_id))
            if source:
                resolved.append(f"{source['title']} ({source['url']})")
        return resolved or ["场景 P0 数据草案，需后续人工核验"]

    def _add_theme_node(
        self,
        nodes: List[Dict[str, object]],
        edges: List[Dict[str, str]],
        evidence: Dict[str, List[str]],
        node_id: str,
        name: str,
        node_type: str,
        venue_id: str,
    ) -> None:
        nodes.append({"id": node_id, "name": name, "type": node_type, "summary": name, "tags": [name], "aliases": [name]})
        edges.append({"source": venue_id, "target": node_id, "relation": "核心主题"})
        evidence[node_id] = ["由场景 P0 数据草案中的点位、任务和文创关系抽取。"]

    def _source_type(self, evidence_text: str) -> str:
        if evidence_text.startswith("由场景 P0"):
            return "derived_from_scene_package"
        if "http" in evidence_text:
            return "public_source"
        if "人工核验" in evidence_text or "P0" in evidence_text:
            return "draft_or_review_needed"
        return "scene_package"

    def _evidence_confidence(self, evidence_text: str) -> str:
        if "http" in evidence_text:
            return "medium"
        if "需后续人工核验" in evidence_text or "P0" in evidence_text:
            return "low"
        return "medium"


