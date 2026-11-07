import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import filters  # noqa: E402
import radar  # noqa: E402
import render  # noqa: E402
import sources  # noqa: E402


class Term(unittest.TestCase):
    def t(self, *texts):
        return filters.classify_term(*texts)

    def test_explicit_summer(self):
        self.assertEqual(self.t("Software Developer Intern (Summer 2027)"), "summer")
        self.assertEqual(self.t("Firmware Intern", "Summer 2027"), "summer")
        self.assertEqual(self.t("ML Co-op S27"), "summer")
        self.assertEqual(self.t("Developer Intern", "Winter 2027, Summer 2027"), "summer")
        self.assertEqual(self.t("Stagiaire développeur - Été 2027"), "summer")
        self.assertEqual(self.t("Intern starting May 2027"), "summer")

    def test_long_terms_covering_summer(self):
        self.assertEqual(self.t("QA / Software Development Co-op (Jan-Dec 2027)"), "covers")
        self.assertEqual(self.t("Co-op Winter 2027 - Software Developer - 8 Months"), "covers")
        self.assertEqual(self.t("Test Automation Co-op (January 2027 - August 2027)"), "covers")
        self.assertEqual(self.t("Developer Co-op", "Winter 2027 · 12 months"), "covers")
        self.assertEqual(self.t("Software Platform Designer Intern September 2026 – August 2027"), "covers")

    def test_rejects_other_terms(self):
        self.assertIsNone(self.t("Software Developer Co-op (Winter 2027)"))
        self.assertIsNone(self.t("Software Developer Co-op - C++ (Winter Term - January - April 2027)"))
        self.assertIsNone(self.t("Developer Intern", "Fall 2026"))
        self.assertIsNone(self.t("Developer Intern", "Summer 2026"))
        self.assertIsNone(self.t("Developer Intern (Fall 2027)"))
        self.assertIsNone(self.t("Software Development Co-op Student (Winter 2026)"))
        self.assertIsNone(self.t("2025 Software Intern"))

    def test_unstated(self):
        self.assertEqual(self.t("Software Engineer Intern"), "unstated")
        self.assertEqual(self.t("Cloud Engineer Intern", "N/A"), "unstated")
        self.assertEqual(self.t("Junior Software Developer Co-op"), "unstated")  # 'junior' is not 'June'


class Role(unittest.TestCase):
    def test_ai(self):
        for title in ["Developer Intern, AI Solutions", "Machine Learning Co-op", "Data Scientist Intern",
                      "Software Engineer Co-op - AI/ML", "LLM Agents Intern", "AI Research Intern"]:
            self.assertEqual(filters.role_type(title), "ai", title)

    def test_software(self):
        for title in ["Software Developer Co-op", "Embedded Software Engineer Co-op Intern",
                      "Firmware Design Intern", "Full Stack Developer (Co-op)", "Cloud Engineer Intern",
                      "QA / Software Development Co-op", "DevOps Developer - Co-op"]:
            self.assertEqual(filters.role_type(title), "swe", title)

    def test_not_software(self):
        for title in ["Hardware Intern - AI HW & System on a Chip", "Sales Operations Co-op",
                      "Optical Test Intern Co-op", "Analog Design Intern", "Junior Project Manager Intern",
                      "Design Co-op (Winter 2027)", "ASIC Engineer Intern"]:
            self.assertIsNone(filters.role_type(title), title)

    def test_hardware_with_software_kept(self):
        self.assertEqual(filters.role_type("Hardware/Software Integration Co-op"), "swe")


class Student(unittest.TestCase):
    def test_levels(self):
        self.assertTrue(filters.is_student_role("Software Developer Co-op"))
        self.assertTrue(filters.is_student_role("Intern – Software Development"))
        self.assertTrue(filters.is_student_role("Stagiaire en développement"))
        self.assertFalse(filters.is_student_role("Senior Software Engineer"))
        self.assertFalse(filters.is_student_role("Software Engineer New Grad"))
        self.assertFalse(filters.is_student_role("Software Engineer"))


class Location(unittest.TestCase):
    def test_places(self):
        self.assertEqual(filters.location_match("Ottawa, ON, Canada"), "ottawa")
        self.assertEqual(filters.location_match("Toronto, ON | Kanata, ON"), "ottawa")
        self.assertEqual(filters.location_match("Nepean, ON K2E 7W6"), "ottawa")
        self.assertEqual(filters.location_match("Gatineau, QC"), "ottawa")
        self.assertEqual(filters.location_match("Remote in Canada"), "remote")
        self.assertEqual(filters.location_match("Canada (Remote)"), "remote")
        self.assertEqual(filters.location_match("Toronto, ON"), "toronto")
        self.assertEqual(filters.location_match("Mississauga, Ontario"), "toronto")
        self.assertEqual(filters.location_match("Markham, ON, Canada"), "toronto")
        self.assertEqual(filters.location_match("Ottawa, ON | Toronto, ON"), "ottawa")
        self.assertIsNone(filters.location_match("New Orleans, LA"))
        self.assertIsNone(filters.location_match("Burlington, VT"))
        self.assertIsNone(filters.location_match("Vancouver, BC"))
        self.assertIsNone(filters.location_match("Waterloo, ON"))
        self.assertIsNone(filters.location_match("Remote"))
        self.assertIsNone(filters.location_match("Remote - US"))


class Dedupe(unittest.TestCase):
    def test_fingerprint_ignores_term_labels_and_order(self):
        a = radar.fingerprint("Ciena Inc.", "Software Developer Intern (Summer 2027)")
        b = radar.fingerprint("Ciena", "Intern, Software Developer - 8 months")
        self.assertEqual(a, b)

    def test_same_url_merges_and_prefers_clear_term(self):
        url = "https://semtech.wd1.myworkdayjobs.com/x/job/Firmware_REQ1"
        rows = [
            {"uid": "workday:a", "company": "Semtech", "title": "Firmware Intern", "location": "Ottawa, ON",
             "url": url, "terms": "", "posted": None, "source": "Semtech"},
            {"uid": "md:" + url, "company": "Semtech", "title": "Firmware Design Intern (Summer 2027)",
             "location": "Ottawa, ON", "url": url + "?src=x", "terms": "", "posted": None, "source": "t"},
        ]
        out = radar.classify(rows, now=2_000_000_000)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["term"], "summer")

    def test_filters_end_to_end(self):
        rows = [
            {"uid": "1", "company": "A", "title": "Software Developer Co-op (Winter 2027)", "location": "Ottawa",
             "url": "https://a/1", "terms": "", "posted": None, "source": "A"},
            {"uid": "2", "company": "B", "title": "Software Developer Co-op", "location": "Toronto, ON",
             "url": "https://b/2", "terms": "Summer 2027", "posted": None, "source": "B"},
            {"uid": "3", "company": "C", "title": "ML Intern", "location": "Kanata, ON",
             "url": "https://c/3", "terms": "Summer 2027", "posted": None, "source": "C"},
        ]
        out = radar.classify(rows, now=2_000_000_000)
        self.assertEqual(sorted(p["company"] for p in out), ["B", "C"])


class Markdown(unittest.TestCase):
    MD = """
| Company | Role | Location | Apply | Date Posted |
|--------|------|----------|:-----:|--------------|
| Ciena | Software Developer Intern (Summer 2027) | Ottawa, ON | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://ciena.example/job/1) | Oct 22, 2026 |
| ↳ | ML Intern | Ottawa, ON | [![Apply](https://img.shields.io/badge/-Apply-blue)](https://ciena.example/job/2) | Oct 23, 2026 |
| Foo | Closed role | Ottawa, ON | Closed🔒 | Oct 1, 2026 |
"""

    def test_parse(self):
        rows = sources.parse_markdown_table(self.MD, "t")
        self.assertEqual([r["url"] for r in rows], ["https://ciena.example/job/1", "https://ciena.example/job/2"])
        self.assertEqual(rows[1]["company"], "Ciena")
        self.assertIsNotNone(rows[0]["posted"])


class Render(unittest.TestCase):
    def test_linkedin_links(self):
        url = render.linkedin_url("software intern", "Toronto, Ontario, Canada")
        self.assertTrue(url.startswith("https://www.linkedin.com/jobs/search/?"))
        self.assertIn("f_E=1", url)
        self.assertIn("location=Toronto", url)

    def test_escaping(self):
        self.assertNotIn("|", render.md_escape("A | B").replace("\\|", ""))
        self.assertEqual(render.md_escape("<script>"), "&lt;script&gt;")
        self.assertIsNone(render.safe_url("javascript:alert(1)"))

    def test_splice_ignores_stamp(self):
        feed1 = "*Updated Monday*\n\nrows"
        feed2 = "*Updated Tuesday*\n\nrows"
        text, changed = render.splice("# T\n", feed1)
        self.assertTrue(changed)
        _, changed = render.splice(text, feed2)
        self.assertFalse(changed)


if __name__ == "__main__":
    unittest.main()
