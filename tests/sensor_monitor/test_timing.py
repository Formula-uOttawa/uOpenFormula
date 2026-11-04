import unittest
from core.sensor_monitor.timing import build_timing, time_intervals
from .test_gear_report import make_run


class TimingTests(unittest.TestCase):
    def test_estimation_requires_explicit_opt_in(self):
        run = make_run([0] * 20, times=[""] * 20)
        self.assertFalse(build_timing(run)["available"])
        estimated = build_timing(run, allow_estimated=True)
        self.assertEqual(estimated["basis"], "estimated")
        self.assertAlmostEqual(estimated["seconds"][-1], 0.95)

    def test_first_to_last_span_is_number_of_gaps(self):
        run = make_run([-1] * 25)
        interval = {"start_sample": 0, "end_sample": 24, "sample_count": 25}
        timed = time_intervals({"intervals": [interval]}, build_timing(run))
        self.assertAlmostEqual(timed[0]["elapsed_span_seconds"], 1.2)

    def test_partial_duplicate_and_nonfinite_times_are_rejected(self):
        for times in (["0", "", "0.1"], [0, 0, 0.1], [0, "nan", 0.1]):
            with self.subTest(times=times), self.assertRaises(ValueError):
                build_timing(make_run([0] * 3, times=times))

    def test_inconsistent_estimation_metadata_is_rejected(self):
        run = make_run([0] * 20, times=[""] * 20)
        run["metadata"]["Duration"] = "1000"
        with self.assertRaises(ValueError):
            build_timing(run, allow_estimated=True)


if __name__ == "__main__":
    unittest.main()
