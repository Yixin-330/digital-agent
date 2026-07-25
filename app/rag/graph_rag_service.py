from __future__ import annotations

from typing import Dict, List

from app.kg.kg_service import CultureKGService


class GraphRAGService:
    def __init__(self, kg_service: CultureKGService) -> None:
        self.kg = kg_service

    def grounded_answer(self, query: str) -> Dict[str, object]:
        subgraph = self.kg.query_subgraph(query)
        nodes: List[Dict[str, object]] = subgraph["nodes"]
        edges: List[Dict[str, str]] = subgraph["edges"]
        citations: List[Dict[str, str]] = subgraph["citations"]
        if not nodes:
            return {
                "answer": "未检索到可靠文化证据，建议补充当前场景中的具体点位、非遗或文创名称。",
                "citations": [],
                "confidence": 0.0,
                "confidence_label": "未命中",
                "evidence_summary": "没有找到可用于回答的图谱节点或来源。",
                "source_quality": {"public_source": 0, "scene_package": 0, "draft_or_review_needed": 0},
                "matched_nodes": [],
                "relations": [],
            }

        primary_nodes = nodes[:3]
        highlights = "、".join(str(node["name"]) for node in primary_nodes)
        details = []
        for node in primary_nodes:
            summary = str(node.get("summary", "")).strip()
            if summary:
                details.append(f"{node['name']}：{summary}")
        relation_text = self._summarize_relations(edges, nodes)
        answer_parts = [
            f"根据当前场景文化知识图谱检索，与你的问题最相关的文化实体包括：{highlights}。",
        ]
        if details:
            answer_parts.append(" ".join(details))
        if relation_text:
            answer_parts.append(relation_text)
        confidence = self._confidence(nodes, citations)
        confidence_label = self._confidence_label(confidence)
        source_quality = self._source_quality(citations)
        answer_parts.append(
            f"可信度：{confidence_label}。以上内容基于当前 P0 场景知识库，动态运营信息仍需以景区现场为准。"
        )
        return {
            "answer": "\n".join(answer_parts),
            "citations": citations,
            "confidence": confidence,
            "confidence_label": confidence_label,
            "evidence_summary": self._evidence_summary(citations, source_quality),
            "source_quality": source_quality,
            "matched_nodes": [
                {
                    "id": str(node.get("id", "")),
                    "name": str(node.get("name", "")),
                    "type": str(node.get("type", "")),
                    "summary": str(node.get("summary", "")),
                }
                for node in primary_nodes
            ],
            "relations": self._relations(edges, nodes),
        }

    def _summarize_relations(self, edges: List[Dict[str, str]], nodes: List[Dict[str, object]]) -> str:
        names = {str(node["id"]): str(node["name"]) for node in nodes}
        relation_samples = []
        for edge in edges[:3]:
            source = names.get(edge["source"])
            target = names.get(edge["target"])
            if source and target:
                relation_samples.append(f"{source} --{edge['relation']}--> {target}")
        if not relation_samples:
            return ""
        return "图谱关系提示：" + "；".join(relation_samples) + "。"

    def _relations(self, edges: List[Dict[str, str]], nodes: List[Dict[str, object]]) -> List[Dict[str, str]]:
        names = {str(node["id"]): str(node["name"]) for node in nodes}
        relations: List[Dict[str, str]] = []
        for edge in edges[:5]:
            source = names.get(edge["source"])
            target = names.get(edge["target"])
            if source and target:
                relations.append({"source": source, "relation": edge["relation"], "target": target})
        return relations

    def _confidence(self, nodes: List[Dict[str, object]], citations: List[Dict[str, str]]) -> float:
        if not nodes:
            return 0.0
        citation_score = min(len(citations) / 4, 1.0) * 0.45
        node_score = min(len(nodes) / 4, 1.0) * 0.3
        public_source_count = sum(1 for item in citations if item.get("source_type") == "public_source")
        source_score = min(public_source_count / 2, 1.0) * 0.25
        return round(min(citation_score + node_score + source_score, 0.95), 2)

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 0.75:
            return "较高"
        if confidence >= 0.45:
            return "中等"
        if confidence > 0:
            return "较低"
        return "未命中"

    def _source_quality(self, citations: List[Dict[str, str]]) -> Dict[str, int]:
        quality = {"public_source": 0, "scene_package": 0, "draft_or_review_needed": 0, "derived_from_scene_package": 0}
        for item in citations:
            source_type = item.get("source_type", "scene_package")
            if source_type not in quality:
                quality[source_type] = 0
            quality[source_type] += 1
        return quality

    def _evidence_summary(self, citations: List[Dict[str, str]], source_quality: Dict[str, int]) -> str:
        if not citations:
            return "没有找到可引用来源。"
        public_count = source_quality.get("public_source", 0)
        draft_count = source_quality.get("draft_or_review_needed", 0) + source_quality.get("derived_from_scene_package", 0)
        return f"命中 {len(citations)} 条引用，其中公开来源 {public_count} 条，场景草案或抽取来源 {draft_count} 条。"

