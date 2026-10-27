import unittest

from backend.domain.plans import sort_plans_for_list


class PlanListSortingTests(unittest.TestCase):
    def test_ideas_then_open_then_closed_by_last_exit(self):
        plans = [
            {
                "id": "closed-old",
                "created_at": "2026-10-01",
                "summary": {"positions": 1, "open": 0, "last_exit_at": "2026-09-01"},
            },
            {
                "id": "open-old",
                "created_at": "2026-10-01",
                "summary": {
                    "positions": 1,
                    "open": 1,
                    "first_entry_at": "2026-09-10",
                    "last_exit_at": None,
                },
            },
            {
                "id": "empty-old",
                "created_at": "2026-10-02",
                "summary": {"positions": 0, "open": 0, "last_exit_at": None},
            },
            {
                "id": "closed-new",
                "created_at": "2026-09-01",
                "summary": {"positions": 1, "open": 0, "last_exit_at": "2026-10-22"},
            },
            {
                "id": "open-new",
                "created_at": "2026-09-01",
                "summary": {
                    "positions": 2,
                    "open": 1,
                    "first_entry_at": "2026-10-21",
                    "last_exit_at": "2026-09-20",
                },
            },
            {
                "id": "empty-new",
                "created_at": "2026-10-22",
                "summary": {"positions": 0, "open": 0, "last_exit_at": None},
            },
        ]

        ordered = sort_plans_for_list(plans)
        self.assertEqual(
            [plan["id"] for plan in ordered],
            [
                "empty-new",
                "empty-old",
                "open-new",
                "open-old",
                "closed-new",
                "closed-old",
            ],
        )

    def test_plan_with_open_and_closed_positions_stays_in_open_group(self):
        plans = [
            {
                "id": "closed",
                "created_at": "2026-10-01",
                "summary": {"positions": 1, "open": 0, "last_exit_at": "2026-10-20"},
            },
            {
                "id": "mixed",
                "created_at": "2026-09-01",
                "summary": {
                    "positions": 2,
                    "open": 1,
                    "first_entry_at": "2026-09-01",
                    "last_exit_at": "2026-10-21",
                },
            },
        ]
        self.assertEqual([plan["id"] for plan in sort_plans_for_list(plans)], ["mixed", "closed"])


if __name__ == "__main__":
    unittest.main()
