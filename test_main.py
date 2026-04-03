import math
import unittest

from main import G, analytical_metrics


class AnalyticalMetricsTests(unittest.TestCase):
    def test_zero_angle_has_zero_height_and_time(self) -> None:
        metrics = analytical_metrics(speed=20, angle_deg=0)
        self.assertAlmostEqual(metrics["flight_time"], 0.0)
        self.assertAlmostEqual(metrics["max_height"], 0.0)
        self.assertAlmostEqual(metrics["range"], 0.0)

    def test_forty_five_degree_solution_matches_closed_form(self) -> None:
        speed = 30
        metrics = analytical_metrics(speed=speed, angle_deg=45)
        expected_range = (speed * speed) / G
        expected_height = (speed * speed) / (4 * G)
        expected_time = (2 * speed * math.sin(math.pi / 4)) / G

        self.assertAlmostEqual(metrics["range"], expected_range, places=6)
        self.assertAlmostEqual(metrics["max_height"], expected_height, places=6)
        self.assertAlmostEqual(metrics["flight_time"], expected_time, places=6)

    def test_complementary_angles_share_the_same_range(self) -> None:
        speed = 42
        lower = analytical_metrics(speed=speed, angle_deg=30)
        higher = analytical_metrics(speed=speed, angle_deg=60)
        self.assertAlmostEqual(lower["range"], higher["range"], places=6)


if __name__ == "__main__":
    unittest.main()
