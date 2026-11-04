import copy
import unittest

from core.sensor_monitor.gear_states import build_gear_states


def make_run(values):
    return {
        "channels": ["Gear Position"],
        "data": [{"Gear Position": str(value)} for value in values],
    }


class ConfirmationTests(unittest.TestCase):
    def test_brief_unexpected_value_is_preserved_but_not_confirmed(self):
        run = make_run([0, 0, 0, 2, 1, 1, 1])
        result = build_gear_states(run)
        states = result["intervals"]
        self.assertEqual([s["status"] for s in states],
                         ["confirmed", "unconfirmed", "confirmed"])
        self.assertEqual([s["value"] for s in states if s["status"] == "confirmed"],
                         [0, 1])
        self.assertEqual(states[1]["start_sample"], 3)

    def test_short_intermediate_gear_is_retained(self):
        states = build_gear_states(make_run([2, 2, 2, 3, 4, 4, 4]))["intervals"]
        self.assertEqual([s["value"] for s in states], [2, 3, 4])
        self.assertEqual(states[1]["status"], "unconfirmed")

    def test_missing_value_prevents_combining_two_short_blocks(self):
        states = build_gear_states(make_run([2, 2, "", 2, 2]))["intervals"]
        self.assertEqual([s["status"] for s in states],
                         ["unconfirmed", "unresolved", "unconfirmed"])
        self.assertEqual(states[1]["kind"], "missing")

    def test_unmapped_negative_and_fractional_values_are_never_confirmed(self):
        states = build_gear_states(make_run([-2] * 4 + [2.6] * 4))["intervals"]
        self.assertTrue(all(s["status"] == "unresolved" for s in states))
        self.assertEqual([s["value"] for s in states], [-2, 2.6])

    def test_invalid_values_break_repetition(self):
        states = build_gear_states(make_run([2, 2, "nan", "inf", "bad", 2]))["intervals"]
        self.assertFalse(any(s["status"] == "confirmed" for s in states))
        self.assertEqual(sum(s["sample_count"] for s in states), 6)

    def test_confirmation_occurs_on_third_sample_and_raw_data_is_unchanged(self):
        run = make_run([4] * 8)
        original = copy.deepcopy(run)
        states = build_gear_states(run)["intervals"]
        self.assertEqual(states[0]["confirmation_sample"], 2)
        self.assertEqual(states[0]["sample_count"], 8)
        self.assertEqual(run, original)

    def test_constant_neutral_is_confirmed_without_declaring_it_healthy(self):
        result = build_gear_states(make_run([0] * 20))
        self.assertEqual(len(result["intervals"]), 1)
        self.assertEqual(result["intervals"][0]["value"], 0)
        self.assertEqual(result["intervals"][0]["status"], "confirmed")
        self.assertNotIn("healthy", result)

    def test_missing_channel_and_empty_data(self):
        self.assertFalse(build_gear_states({"channels": [], "data": []})["available"])
        self.assertEqual(build_gear_states(make_run([]))["intervals"], [])

    def test_confirmation_setting_is_validated_and_changes_acceptance(self):
        run = make_run([2, 2])
        self.assertEqual(
            build_gear_states(run, confirmation_samples=2)["intervals"][0]["status"],
            "confirmed",
        )
        self.assertEqual(
            build_gear_states(run, confirmation_samples=3)["intervals"][0]["status"],
            "unconfirmed",
        )
        for setting in (True, 0, 1, 2.5, "3"):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                build_gear_states(run, confirmation_samples=setting)


if __name__ == "__main__":
    unittest.main()
