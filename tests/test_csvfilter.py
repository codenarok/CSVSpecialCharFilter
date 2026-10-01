import io
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csvfilter

SAMPLE = (
    "Title,Developer,Price\n"
    "Normal Game,Normal Studio,9.99\n"
    "Café Adventure,Gaming Inc,14.99\n"
    "Simple Puzzle,Tést Studios,4.99\n"
    "Pokémon Quest,Regular Dev,19.99\n"
    "Test Game,Émoji Games 😀,0.99\n"
)


class TempDirCase(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def path(self, name):
        return os.path.join(self._dir.name, name)

    def write(self, name, text, encoding="utf-8"):
        with open(self.path(name), "w", newline="", encoding=encoding) as handle:
            handle.write(text)
        return self.path(name)

    def read(self, name):
        with open(self.path(name), newline="", encoding="utf-8") as handle:
            return handle.read()


class DetectionTests(unittest.TestCase):
    def test_plain_ascii_is_not_special(self):
        for text in ["Normal text", "Price: $50", "x09 \\ {}~", "Hello\tWorld", "Hello\r\nWorld", "", None]:
            self.assertFalse(csvfilter.contains_special_characters(text), repr(text))

    def test_non_ascii_and_control_characters_are_special(self):
        for text in ["Café", "Résumé", "emoji 😀", "smart ’quote’", "non breaking", "bell\x07", "nul\x00"]:
            self.assertTrue(csvfilter.contains_special_characters(text), repr(text))

    def test_find_special_keeps_repeats(self):
        self.assertEqual(csvfilter.find_special("éé à"), ["é", "é", "à"])


class ToAsciiTests(unittest.TestCase):
    def test_accents_are_dropped(self):
        self.assertEqual(csvfilter.to_ascii("Café Résumé Pokémon"), "Cafe Resume Pokemon")

    def test_turkish_letters(self):
        self.assertEqual(csvfilter.to_ascii("İstanbul ışık şeker çağ öğün"), "Istanbul isik seker cag ogun")

    def test_typography_and_symbols(self):
        self.assertEqual(csvfilter.to_ascii("“Hi” – it’s… 5 €"), '"Hi" - it\'s... 5 EUR')
        self.assertEqual(csvfilter.to_ascii("a b ™ ß"), "a b TM ss")

    def test_placeholder_for_the_rest(self):
        self.assertEqual(csvfilter.to_ascii("ok 😀 日本"), "ok ? ??")
        self.assertEqual(csvfilter.to_ascii("ok 😀", placeholder=""), "ok ")

    def test_result_is_always_ascii(self):
        cleaned = csvfilter.to_ascii("".join(chr(code) for code in range(0x80, 0x3000)))
        self.assertFalse(csvfilter.contains_special_characters(cleaned))


class ProcessTests(TempDirCase):
    def test_filter_writes_only_matching_rows_unchanged(self):
        source = self.write("in.csv", SAMPLE)
        stats = csvfilter.run(source, self.path("out.csv"), ["Title", "Developer"])
        self.assertEqual((stats.total_rows, stats.matching_rows, stats.rows_written), (5, 4, 4))
        self.assertEqual(
            self.read("out.csv"),
            "Title,Developer,Price\n"
            "Café Adventure,Gaming Inc,14.99\n"
            "Simple Puzzle,Tést Studios,4.99\n"
            "Pokémon Quest,Regular Dev,19.99\n"
            "Test Game,Émoji Games 😀,0.99\n",
        )
        self.assertEqual(stats.per_column, {"Title": 2, "Developer": 2})
        self.assertEqual(stats.characters["é"], 3)

    def test_only_chosen_columns_are_checked(self):
        source = self.write("in.csv", SAMPLE)
        stats = csvfilter.process(source, ["Title"])
        self.assertEqual(stats.matching_rows, 2)

    def test_all_columns_by_default(self):
        source = self.write("in.csv", "a,b\nx,é\n")
        self.assertEqual(csvfilter.process(source).matching_rows, 1)

    def test_clean_writes_every_row_as_ascii(self):
        source = self.write("in.csv", SAMPLE)
        stats = csvfilter.run(source, self.path("out.csv"), mode="clean")
        self.assertEqual(stats.rows_written, 5)
        cleaned = self.read("out.csv")
        self.assertFalse(csvfilter.contains_special_characters(cleaned))
        self.assertIn("Cafe Adventure,Gaming Inc", cleaned)
        self.assertIn("Emoji Games ?", cleaned)

    def test_clean_leaves_unchosen_columns_alone(self):
        source = self.write("in.csv", "a,b\né,é\n")
        csvfilter.run(source, self.path("out.csv"), ["a"], mode="clean")
        self.assertEqual(self.read("out.csv"), "a,b\ne,é\n")

    def test_quoted_fields_with_commas_and_newlines_survive(self):
        source = self.write("in.csv", 'a,b\n"é, with comma","line one\nline two"\n')
        output = io.StringIO()
        csvfilter.process(source, output=output)
        self.assertEqual(output.getvalue(), 'a,b\n"é, with comma","line one\nline two"\n')

    def test_short_rows_do_not_crash(self):
        source = self.write("in.csv", "a,b,c\nonly one\nx,y,é\n")
        self.assertEqual(csvfilter.process(source, ["c"]).matching_rows, 1)

    def test_semicolon_delimiter_is_detected_and_kept(self):
        source = self.write("in.csv", "a;b\né;1\nx;2\n")
        output = io.StringIO()
        stats = csvfilter.process(source, ["a"], output=output)
        self.assertEqual(stats.delimiter, ";")
        self.assertEqual(output.getvalue(), "a;b\né;1\n")

    def test_utf8_bom_is_not_reported(self):
        source = self.write("in.csv", "a,b\nx,y\n", encoding="utf-8-sig")
        stats = csvfilter.process(source)
        self.assertEqual(stats.header, ["a", "b"])
        self.assertFalse(stats.found)

    def test_wrong_encoding_gives_a_helpful_error(self):
        source = self.write("in.csv", "a\ncafé\n", encoding="cp1252")
        with self.assertRaisesRegex(csvfilter.CSVFilterError, "cp1252"):
            csvfilter.process(source)
        self.assertEqual(csvfilter.process(source, encoding="cp1252").matching_rows, 1)

    def test_unknown_column_lists_the_available_ones(self):
        source = self.write("in.csv", SAMPLE)
        with self.assertRaisesRegex(csvfilter.CSVFilterError, "Nope.*Available columns: Title"):
            csvfilter.process(source, ["Nope"])

    def test_empty_and_missing_files(self):
        with self.assertRaisesRegex(csvfilter.CSVFilterError, "empty"):
            csvfilter.process(self.write("empty.csv", ""))
        with self.assertRaisesRegex(csvfilter.CSVFilterError, "Cannot open"):
            csvfilter.process(self.path("missing.csv"))

    def test_header_only_file(self):
        stats = csvfilter.process(self.write("in.csv", "a,b\n"))
        self.assertEqual((stats.total_rows, stats.found), (0, False))
        self.assertIn("0 rows x 2 columns", csvfilter.format_report(stats))

    def test_refuses_to_overwrite_the_input(self):
        source = self.write("in.csv", SAMPLE)
        with self.assertRaisesRegex(csvfilter.CSVFilterError, "different"):
            csvfilter.run(source, source)
        self.assertEqual(self.read("in.csv"), SAMPLE)

    def test_failed_run_keeps_an_existing_output_file(self):
        source = self.write("in.csv", SAMPLE)
        self.write("out.csv", "keep me")
        with self.assertRaises(csvfilter.CSVFilterError):
            csvfilter.run(source, self.path("out.csv"), ["Nope"])
        self.assertEqual(self.read("out.csv"), "keep me")
        self.assertEqual(sorted(os.listdir(self._dir.name)), ["in.csv", "out.csv"])

    def test_excel_safe_neutralises_formulas_but_not_numbers(self):
        source = self.write("in.csv", 'a,b\né,"=HYPERLINK(""http://x"")"\né,-5.5\né,@cmd\n')
        output = io.StringIO()
        csvfilter.process(source, ["a"], output=output, make_excel_safe=True)
        self.assertEqual(
            output.getvalue(),
            'a,b\né,"\'=HYPERLINK(""http://x"")"\né,-5.5\né,\'@cmd\n',
        )


class ReportAndCliTests(TempDirCase):
    def test_report_names_the_characters(self):
        stats = csvfilter.process(self.write("in.csv", SAMPLE))
        report = csvfilter.format_report(stats)
        self.assertIn("5 rows x 3 columns", report)
        self.assertIn("4 (80.0%)", report)
        self.assertIn("U+00E9 LATIN SMALL LETTER E WITH ACUTE (é)", report)
        self.assertIn("'Café Adventure' -> 'Cafe Adventure'", report)

    def test_check_exit_status(self):
        dirty = self.write("dirty.csv", SAMPLE)
        clean = self.write("clean.csv", "a,b\nx,y\n")
        self.assertEqual(csvfilter.main([dirty, "--check", "-q"]), 1)
        self.assertEqual(csvfilter.main([clean, "--check", "-q"]), 0)
        self.assertEqual(csvfilter.main([self.path("missing.csv"), "-q"]), 2)

    def test_cli_clean_to_file(self):
        source = self.write("in.csv", SAMPLE)
        status = csvfilter.main([source, "--clean", "-c", "Title", "-o", self.path("out.csv"), "-q"])
        self.assertEqual(status, 0)
        self.assertIn("Cafe Adventure", self.read("out.csv"))
        self.assertIn("Tést Studios", self.read("out.csv"))


if __name__ == "__main__":
    unittest.main()
