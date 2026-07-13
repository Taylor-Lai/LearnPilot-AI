from backend.app.adapters.llm_adapter import LLMAdapter


class TutorAgent:
    name = "TutorAgent"

    def __init__(self, llm: LLMAdapter | None = None) -> None:
        self.llm = llm or LLMAdapter()

    def run(self, question: str, profile: dict | None = None, history: list[str] | None = None) -> dict:
        return self.llm.tutor_answer(question)
