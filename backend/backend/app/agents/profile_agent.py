from backend.app.adapters.llm_adapter import LLMAdapter


class ProfileAgent:
    name = "ProfileAgent"

    def __init__(self, llm: LLMAdapter | None = None) -> None:
        self.llm = llm or LLMAdapter()

    def run(self, text: str) -> dict:
        return self.llm.profile_from_text(text)
