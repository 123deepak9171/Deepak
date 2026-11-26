"""Fast unit tests (no rendering): python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))

from dmw import captions, ff, planner  # noqa: E402
from dmw.config import JobError, safe_path  # noqa: E402


class SilenceTests(unittest.TestCase):
    def test_speech_intervals_cut_gaps(self):
        keep = ff.speech_intervals(0, 10, [(2.5, 4.0), (6.5, 7.5)], padding=0.1, min_keep=0.3)
        self.assertEqual(keep, [(0, 2.6), (3.9, 6.6), (7.4, 10)])

    def test_leading_and_trailing_silence(self):
        keep = ff.speech_intervals(0, 10, [(0, 1.0), (9.0, float("inf"))], padding=0.0, min_keep=0.3)
        self.assertEqual(keep, [(1.0, 9.0)])


class PlannerTests(unittest.TestCase):
    def test_instruction_keywords(self):
        job = {"instructions": "YouTube ke liye cinematic video, 2 minute", "timeline": []}
        notes = planner.apply_instructions(job)
        self.assertEqual(job["aspect"], "16:9")
        self.assertEqual(job["style"], "cinematic")
        self.assertEqual(job["target_duration"], 120)
        self.assertTrue(notes)

    def test_reel_beats_youtube(self):
        job = {"instructions": "youtube shorts reel banao 30 sec"}
        planner.apply_instructions(job)
        self.assertEqual(job["aspect"], "9:16")
        self.assertEqual(job["target_duration"], 30)

    def test_path_outside_repo_rejected(self):
        with self.assertRaises(JobError):
            safe_path("../../etc/passwd", must_exist=False)


class CaptionTests(unittest.TestCase):
    def test_script_timing_covers_speech(self):
        words = captions.words_from_script("ek do teen char paanch", [(1.0, 3.0), (4.0, 5.0)])
        self.assertEqual(len(words), 5)
        self.assertGreaterEqual(words[0]["start"], 1.0)
        self.assertLessEqual(words[-1]["end"], 5.0001)

    def test_chunking_respects_max_words(self):
        w = [{"text": str(i), "start": i * 0.3, "end": i * 0.3 + 0.25} for i in range(7)]
        self.assertTrue(all(len(c) <= 3 for c in captions.chunk_words(w, 3)))


if __name__ == "__main__":
    unittest.main()
