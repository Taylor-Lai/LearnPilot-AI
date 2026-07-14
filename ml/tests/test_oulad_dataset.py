from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from ml_service.datasets.io import load_dataset
from ml_service.datasets.oulad import prepare_oulad_dataset
from ml_service.training.workflow import build_training_rows


class OuladDatasetTest(unittest.TestCase):
    def test_preprocessor_emits_valid_privacy_bounded_training_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            output = root / "processed"
            source.mkdir()
            self._write_fixture(source)

            manifest = prepare_oulad_dataset(source, output, max_events=4, max_events_per_student=2)
            graph, resources, students, events = load_dataset(output)
            rows, groups = build_training_rows(output)

            self.assertEqual(manifest["license"], "CC BY 4.0")
            self.assertFalse(manifest["protected_attributes_used"])
            self.assertEqual(len(events), 4)
            self.assertEqual(len(students), 2)
            self.assertEqual(len(rows), 4)
            self.assertEqual(len(groups), 4)
            self.assertTrue(all(student["student_id"].startswith("oulad_") for student in students))
            serialized = json.dumps(students, ensure_ascii=False)
            for forbidden in ("gender", "region", "age_band", "disability", "imd_band", "student-one"):
                self.assertNotIn(forbidden, serialized)
            self.assertIn("AAA:module", {node.name for node in graph})
            self.assertEqual({resource.style for resource in resources}, {"text", "quiz"})

    @staticmethod
    def _write_fixture(root: Path) -> None:
        _write_csv(
            root / "studentInfo.csv",
            [
                "code_module",
                "code_presentation",
                "id_student",
                "gender",
                "region",
                "highest_education",
                "imd_band",
                "age_band",
                "num_of_prev_attempts",
                "studied_credits",
                "disability",
                "final_result",
            ],
            [
                ["AAA", "2013J", "student-one", "F", "North", "A Level", "0-10%", "0-35", 0, 60, "N", "Pass"],
                ["AAA", "2013J", "student-two", "M", "South", "A Level", "90-100%", "35-55", 1, 60, "Y", "Fail"],
            ],
        )
        _write_csv(
            root / "assessments.csv",
            ["code_module", "code_presentation", "id_assessment", "assessment_type", "date", "weight"],
            [["AAA", "2013J", 1, "TMA", 20, 100]],
        )
        _write_csv(
            root / "studentAssessment.csv",
            ["id_assessment", "id_student", "date_submitted", "is_banked", "score"],
            [[1, "student-one", 18, 0, 80], [1, "student-two", 19, 0, 35]],
        )
        _write_csv(
            root / "vle.csv",
            ["id_site", "code_module", "code_presentation", "activity_type", "week_from", "week_to"],
            [[101, "AAA", "2013J", "oucontent", 1, 2], [102, "AAA", "2013J", "quiz", 1, 2]],
        )
        _write_csv(
            root / "studentVle.csv",
            ["code_module", "code_presentation", "id_student", "id_site", "date", "sum_click"],
            [
                ["AAA", "2013J", "student-one", 101, 1, 1],
                ["AAA", "2013J", "student-one", 102, 2, 12],
                ["AAA", "2013J", "student-two", 101, 1, 1],
                ["AAA", "2013J", "student-two", 102, 2, 15],
            ],
        )


def _write_csv(path: Path, fieldnames: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(fieldnames)
        writer.writerows(rows)


if __name__ == "__main__":
    unittest.main()
