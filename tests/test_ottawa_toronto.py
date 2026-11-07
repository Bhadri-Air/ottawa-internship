"""The two rules this fork adds: Ottawa + Toronto only, and Summer 2027 only."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import LOOSE, STRICT, Posting, area_label, classify, term_label  # noqa: E402


def tier(title, location="Toronto, ON, Canada", raw=None):
    return classify(Posting("Acme", title, location, "https://e.com/j", "test", raw=raw or {})).tier


class TestCities(unittest.TestCase):
    def test_ottawa_area_is_kept(self):
        for loc in ["Ottawa, ON", "Ottawa, Ontario, Canada", "Kanata, ON", "Nepean, Ontario",
                    "Gatineau, QC", "Barrhaven, ON", "Orléans, ON", "Canada - Ottawa (Bill Leathem)",
                    "CAN Kanata (2), ON - WR", "YOW B"]:
            with self.subTest(loc=loc):
                self.assertEqual(tier("Machine Learning Intern", loc), STRICT)

    def test_toronto_area_is_kept(self):
        for loc in ["Toronto, ON", "Mississauga, ON, Canada", "Markham, Ontario", "North York, ON",
                    "Vaughan, ON", "Oakville, ON", "Richmond Hill, ON", "Greater Toronto Area"]:
            with self.subTest(loc=loc):
                self.assertEqual(tier("Machine Learning Intern", loc), STRICT)

    def test_rest_of_ontario_is_rejected(self):
        for loc in ["Waterloo, ON", "Kitchener, ON", "Hamilton, ON", "Guelph, Ontario",
                    "London, ON", "Kingston, Ontario", "Sault Ste. Marie, ON"]:
            with self.subTest(loc=loc):
                self.assertIsNone(tier("Machine Learning Intern", loc))

    def test_us_ottawa_is_rejected(self):
        self.assertIsNone(tier("Machine Learning Intern", "Ottawa, IL"))

    def test_shared_listing_kept(self):
        self.assertEqual(tier("Machine Learning Intern", "Waterloo, ON | Ottawa, ON"), STRICT)

    def test_remote_canada_kept(self):
        self.assertEqual(tier("Machine Learning Intern", "Remote, Canada"), STRICT)

    def test_area_label(self):
        self.assertEqual(area_label("Kanata, ON"), "Ottawa")
        self.assertEqual(area_label("Mississauga, ON, Canada"), "Toronto")
        self.assertEqual(area_label("Ottawa, ON; Toronto, ON"), "Ottawa / Toronto")
        self.assertEqual(area_label("Remote in Canada"), "Remote")


class TestSummerOnly(unittest.TestCase):
    def test_summer_kept(self):
        for title in ["ML Intern, Summer 2027", "ML Intern (S27)", "ML Intern (May 2027 - 12 Months)",
                      "ML Intern, Summer", "Summer 2027 Intern, Machine Learning",
                      "2027 Summer – AI Developer Intern"]:
            with self.subTest(title=title):
                self.assertEqual(tier(title), STRICT)

    def test_winter_rejected(self):
        for title in ["ML Intern, Winter 2027", "ML Intern (W27)", "AI Co-op, Winter",
                      "ML Intern (January 2027 - 12 months)", "ML Co-op (Jan-Aug 2027)",
                      "2027 Winter – AI Developer Intern", "ML Co-op (Winter 2027) - 8 months",
                      "ML Intern, Spring 2027", "AI Intern, Spring", "ML Co-op (Spring)"]:
            with self.subTest(title=title):
                self.assertIsNone(tier(title))

    def test_fall_rejected(self):
        for title in ["ML Intern, Fall 2026", "ML Intern, Fall 2027", "ML Intern, Fall"]:
            with self.subTest(title=title):
                self.assertIsNone(tier(title))

    def test_term_in_tracker_field(self):
        self.assertIsNone(tier("Software Developer Intern", raw={"terms": ["Winter 2027"]}))
        self.assertEqual(tier("Software Developer Intern", raw={"terms": ["Summer 2027"]}), LOOSE)

    def test_no_term_kept(self):
        self.assertEqual(tier("Machine Learning Intern"), STRICT)
        self.assertEqual(tier("Software Developer Co-op"), LOOSE)

    def test_spring_boot_is_not_a_season(self):
        self.assertEqual(tier("Spring Boot Developer Intern"), LOOSE)
        self.assertEqual(tier("Java Spring Developer Co-op"), LOOSE)

    def test_label(self):
        post = Posting("Acme", "Software Developer Intern (May 2027 - 12 Months)", "Toronto", "u", "t")
        self.assertEqual(term_label(post), "Summer 2027")


if __name__ == "__main__":
    unittest.main()
