import unittest

from backend.app.agents.tutor_agent import TutorAgent


class _RecordingLLM:
    def __init__(self) -> None:
        self.arguments = None

    def tutor_answer(self, question, profile, history, evidence):
        self.arguments = (question, profile, history, evidence)
        return {"answer": "ok", "hints": [], "next_action": "done"}


class TutorAgentTest(unittest.TestCase):
    def test_forwards_profile_history_and_evidence(self) -> None:
        llm = _RecordingLLM()
        agent = TutorAgent(llm=llm)
        profile = {"course": "人工智能", "knowledge_level": "beginner"}
        history = ["上一轮问题"]
        evidence = [{"title": "卷积神经网络", "snippet": "局部感受野"}]

        result = agent.run("为什么卷积能提取局部特征？", profile, history, evidence)

        self.assertEqual(result["answer"], "ok")
        self.assertEqual(llm.arguments, ("为什么卷积能提取局部特征？", profile, history, evidence))


if __name__ == "__main__":
    unittest.main()
