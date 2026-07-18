from ml_service.application.resource_formats import ResourceBundleBuilder


def test_structured_practice_keeps_question_rows() -> None:
    builder = ResourceBundleBuilder()
    rows = builder._structured_practice(
        [
            {
                "question": "解释线性回归的损失函数。",
                "answer": "均方误差衡量预测值与真实值的平均平方差。",
                "evidence_refs": ["线性回归讲义"],
            }
        ]
    )

    assert rows == [
        {
            "question": "解释线性回归的损失函数。",
            "answer": "均方误差衡量预测值与真实值的平均平方差。",
            "evidence_refs": ["线性回归讲义"],
        }
    ]


def test_practice_markdown_never_exposes_python_repr() -> None:
    builder = ResourceBundleBuilder()
    markdown = builder._practice_markdown(
        {
            "practice": "[{'question': '实现一个线性回归预测。', 'answer': '使用 fit 和 predict。'}]"
        }
    )

    assert markdown == "1. 实现一个线性回归预测。"
    assert "{'question'" not in markdown
