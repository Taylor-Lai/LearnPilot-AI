"""Seed evaluation questions for a course (idempotent).

Usage (local MySQL):
  cd backend
  python scripts/seed_course_questions.py

Usage (Render PostgreSQL):
  set DATABASE_URL=postgresql://...
  python scripts/seed_course_questions.py --course-id 1

Verify:
  GET /api/v1/courses/1/questions
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.database import SessionLocal
from backend.app.models import Course, KnowledgePoint, Question

DEFAULT_COURSE_ID = 1
MIN_QUESTIONS = 5

COURSE_QUESTIONS: dict[int, list[dict]] = {
    1: [
        {
            "question_type": "true_false",
            "stem": "机器学习是让计算机从数据中自动学习规律，而不是依赖人工逐条编写全部规则。",
            "answer": "true",
            "explanation": "机器学习强调从样本中归纳模式，而不是完全依赖硬编码规则。",
            "difficulty": 0.4,
            "knowledge_point": "机器学习基础",
            "source": "seed:course_questions:ai",
        },
        {
            "question_type": "true_false",
            "stem": "卷积神经网络（CNN）只能处理文本数据，不能用于图像任务。",
            "answer": "false",
            "explanation": "CNN 最初就是为图像等网格数据设计的特征提取模型。",
            "difficulty": 0.45,
            "knowledge_point": "CNN",
            "source": "seed:course_questions:ai",
        },
        {
            "question_type": "short_answer",
            "stem": "请用一句话说明反向传播算法在神经网络训练中的作用。",
            "answer": "根据损失函数计算梯度并反向更新网络参数",
            "explanation": "反向传播通过链式法则把输出误差传递到各层参数。",
            "difficulty": 0.55,
            "knowledge_point": "反向传播",
            "source": "seed:course_questions:ai",
        },
        {
            "question_type": "short_answer",
            "stem": "什么是决策树？它常用于哪类机器学习任务？",
            "answer": "通过树形结构进行特征划分，常用于分类和回归",
            "explanation": "决策树通过递归划分特征空间完成预测。",
            "difficulty": 0.5,
            "knowledge_point": "决策树",
            "source": "seed:course_questions:ai",
        },
        {
            "question_type": "true_false",
            "stem": "梯度下降法在任意初始点都一定能找到全局最优解。",
            "answer": "false",
            "explanation": "非凸优化中梯度下降可能陷入局部最优或鞍点。",
            "difficulty": 0.5,
            "knowledge_point": "梯度下降",
            "source": "seed:course_questions:ai",
        },
        {
            "question_type": "short_answer",
            "stem": "请解释“过拟合”是什么意思，并给出一个常见缓解方法。",
            "answer": "模型在训练集表现很好但泛化差，可通过正则化或增加数据缓解",
            "explanation": "过拟合通常表现为训练误差低、验证误差高。",
            "difficulty": 0.6,
            "knowledge_point": "模型评估",
            "source": "seed:course_questions:ai",
        },
    ],
    2: [
        {
            "question_type": "true_false",
            "stem": "支持向量机的目标是找到一个最大间隔分离超平面。",
            "answer": "true",
            "explanation": "SVM 通过最大化间隔提升泛化能力。",
            "difficulty": 0.5,
            "knowledge_point": "支持向量机",
            "source": "seed:course_questions:ml",
        },
        {
            "question_type": "short_answer",
            "stem": "K-Means 聚类算法属于哪一类学习？请简要说明。",
            "answer": "无监督学习，通过最小化簇内距离划分样本",
            "explanation": "K-Means 不需要标签，只根据样本相似性聚类。",
            "difficulty": 0.45,
            "knowledge_point": "聚类算法",
            "source": "seed:course_questions:ml",
        },
    ],
}


def _match_knowledge_point(
    session,
    course_id: int,
    knowledge_point_name: str | None,
) -> KnowledgePoint | None:
    if not knowledge_point_name:
        return None
    return (
        session.query(KnowledgePoint)
        .filter(
            KnowledgePoint.course_id == course_id,
            KnowledgePoint.name == knowledge_point_name,
        )
        .first()
    )


def _question_exists(session, course_id: int, stem: str) -> bool:
    return session.query(Question.id).filter(Question.course_id == course_id, Question.stem == stem).first() is not None


def seed_course_questions(course_id: int = DEFAULT_COURSE_ID, min_questions: int = MIN_QUESTIONS) -> int:
    items = COURSE_QUESTIONS.get(course_id, [])
    if not items:
        raise ValueError(f"No seed template found for course_id={course_id}")

    created = 0
    with SessionLocal() as session:
        course = session.get(Course, course_id)
        if course is None:
            raise RuntimeError(f"course_id={course_id} does not exist. Initialize courses first.")

        existing_count = session.query(Question).filter(Question.course_id == course_id).count()
        if existing_count >= min_questions:
            print(
                f"Skip seeding: course_id={course_id} already has {existing_count} questions "
                f"(required >= {min_questions})."
            )
            return 0

        try:
            for item in items:
                stem = item["stem"]
                if _question_exists(session, course_id, stem):
                    continue

                knowledge_point = _match_knowledge_point(
                    session,
                    course_id,
                    item.get("knowledge_point"),
                )
                session.add(
                    Question(
                        course_id=course_id,
                        knowledge_point_id=knowledge_point.id if knowledge_point else None,
                        question_type=item["question_type"],
                        stem=stem,
                        answer=item.get("answer"),
                        explanation=item.get("explanation"),
                        difficulty=float(item.get("difficulty", 0.5)),
                        source=item.get("source"),
                    )
                )
                created += 1

            session.commit()
        except Exception:
            session.rollback()
            raise

        total = session.query(Question).filter(Question.course_id == course_id).count()

    print(f"Seeded {created} questions for course_id={course_id}.")
    print(f"Total questions for course_id={course_id}: {total}")
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed course evaluation questions")
    parser.add_argument("--course-id", type=int, default=DEFAULT_COURSE_ID)
    parser.add_argument("--min-questions", type=int, default=MIN_QUESTIONS)
    args = parser.parse_args()

    seed_course_questions(course_id=args.course_id, min_questions=args.min_questions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
