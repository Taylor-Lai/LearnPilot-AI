from backend.app.adapters.ml_adapter import MLAdapter


class EvaluatorAgent:
    name = "EvaluatorAgent"

    def __init__(self, ml: MLAdapter | None = None) -> None:
        self.ml = ml or MLAdapter()

    def run(
        self,
        correct_count: int,
        total_count: int,
        completed_resource_count: int,
        study_minutes: int,
    ) -> dict:
        return self.ml.evaluate_mastery(correct_count, total_count, completed_resource_count, study_minutes)
