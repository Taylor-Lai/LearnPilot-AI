from __future__ import annotations

import os
import unittest

os.environ.setdefault("DATABASE_MODE", "sqlite")
os.environ.setdefault("SQLITE_DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("USE_ML_SERVICE", "false")
os.environ.setdefault("LEARNPILOT_LLM_MODE", "template")

from backend.app.api.producer import _merge_ml_generation


class ProducerMlBridgeTest(unittest.TestCase):
    def test_ml_resource_bundle_enriches_legacy_frontend_shape(self) -> None:
        local_result = {
            "topic": "CNN",
            "lecture": {"title": "旧讲义", "content": "旧内容"},
            "videos": [],
            "agent_traces": [{"agent": "本地生成器"}],
        }
        ml_result = {
            "generated_cards": [
                {
                    "resource_bundle": {
                        "title": "CNN 个性化资源包",
                        "formats": {
                            "lecture": {"markdown": "# CNN\n个性化讲义"},
                            "mind_map": {
                                "mermaid": "mindmap\n  root((CNN))",
                                "nodes": [{"id": "cnn", "label": "CNN"}],
                                "edges": [],
                            },
                            "quiz_bank": {
                                "questions": [
                                    {
                                        "id": "q1",
                                        "type": "short_answer",
                                        "prompt": "卷积核的作用是什么？",
                                        "answer": "提取局部特征",
                                        "rubric": ["说明局部感受野"],
                                    }
                                ]
                            },
                            "video_storyboard": {
                                "scenes": [
                                    {
                                        "visual": "卷积核移动",
                                        "narration": "观察卷积核如何提取局部特征。",
                                    }
                                ]
                            },
                        },
                    },
                    "quality_check": {"passed": True},
                    "review_cycle": {"attempts": 1},
                    "safety_meta": {"safe": True},
                    "rag_context": [{"resource_id": "r1"}],
                }
            ],
            "agent_traces": [{"agent": "RAG 检索智能体"}],
        }

        merged = _merge_ml_generation(local_result, ml_result)

        self.assertEqual(merged["lecture"]["title"], "CNN 个性化资源包")
        self.assertIn("个性化讲义", merged["lecture"]["content"])
        self.assertEqual(merged["exercises"][0]["answer"], "提取局部特征")
        self.assertIn("mindmap", merged["mind_map"]["content"])
        self.assertTrue(merged["generation_quality"]["passed"])
        self.assertEqual(len(merged["agent_traces"]), 2)
        self.assertTrue(merged["videos"][0]["generated"])
        self.assertIn("卷积核移动", merged["videos"][0]["animation_html"])

    def test_ml_bridge_drops_invalid_quiz_rows(self) -> None:
        local_result = {
            "topic": "Python",
            "lecture": {"title": "旧讲义", "content": "旧内容"},
            "videos": [],
            "agent_traces": [],
        }
        ml_result = {
            "generated_cards": [{
                "resource_bundle": {"formats": {"quiz_bank": {"questions": [
                    {"id": "bad", "type": "short_answer", "prompt": ""},
                    {"id": "ok", "type": "short_answer", "prompt": "解释变量。", "answer": "变量保存值。"},
                ]}}},
                "rag_context": [],
            }],
        }

        merged = _merge_ml_generation(local_result, ml_result)

        self.assertEqual(len(merged["exercises"]), 1)
        self.assertEqual(merged["exercises"][0]["question"], "解释变量。")


if __name__ == "__main__":
    unittest.main()
