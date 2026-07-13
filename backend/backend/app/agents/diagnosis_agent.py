from backend.app.adapters.ml_adapter import MLAdapter


class DiagnosisAgent:
    name = "DiagnosisAgent"

    def __init__(self, ml: MLAdapter | None = None) -> None:
        self.ml = ml or MLAdapter()

    def run(self, profile: dict) -> list[dict]:
        return self.ml.diagnose_weakness(profile)
