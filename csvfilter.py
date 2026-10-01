#!/usr/bin/env python3
"""Find, report and clean non-ASCII characters in CSV files.

Standard library only. Files are read row by row, so large files are fine.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional, Sequence, TextIO

__version__ = "1.1.1"

# Anything outside printable ASCII plus tab, newline and carriage return.
SPECIAL = re.compile(r"[^\x09\x0A\x0D\x20-\x7E]")

# Characters with an obvious ASCII spelling that Unicode decomposition misses.
_ASCII_SPELLINGS = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-",
    "−": "-", "•": "*", "·": "*",
    "ß": "ss", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE",
    "ø": "o", "Ø": "O", "ł": "l", "Ł": "L",
    "đ": "d", "Đ": "D", "ı": "i", "þ": "th", "Þ": "Th",
    "ð": "d", "Ð": "D",
    "€": "EUR", "£": "GBP", "¥": "JPY",
    "©": "(C)", "®": "(R)", "×": "x", "÷": "/",
}

# Mojibake: UTF-8 bytes that were read as cp1252 or Latin-1, so "Café" shows
# as "CafÃ©". Map each character such a misreading can produce back to its byte.
_BYTE_OF = {chr(byte): byte for byte in range(0x80, 0x100)}
for _byte in range(0x80, 0xA0):
    try:
        _BYTE_OF[bytes([_byte]).decode("cp1252")] = _byte
    except UnicodeDecodeError:
        pass


def _chars_for(first: int, last: int) -> str:
    return "".join(re.escape(char) for char, byte in _BYTE_OF.items() if first <= byte <= last)


_CONTINUATION = _chars_for(0x80, 0xBF)
_MOJIBAKE = re.compile(
    f"[{_chars_for(0xC2, 0xDF)}][{_CONTINUATION}]"
    f"|[{_chars_for(0xE0, 0xEF)}][{_CONTINUATION}]{{2}}"
    f"|[{_chars_for(0xF0, 0xF4)}][{_CONTINUATION}]{{3}}"
)

_DELIMITERS = ",;\t|"
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")


class CSVFilterError(Exception):
    """A problem the user can fix: bad path, wrong encoding, unknown column."""


def find_special(text: Optional[str]) -> list[str]:
    """Return every special character in text, in order, with repeats."""
    if not text:
        return []
    return SPECIAL.findall(text)


def contains_special_characters(text: Optional[str]) -> bool:
    return bool(text) and SPECIAL.search(text) is not None


def to_ascii(text: str, placeholder: str = "?") -> str:
    """Replace special characters with the closest ASCII spelling.

    Accents are dropped (e-acute becomes e), typographic quotes and dashes
    become plain ones, and anything with no ASCII spelling becomes placeholder.
    """
    if not contains_special_characters(text):
        return text

    def replace(match: "re.Match[str]") -> str:
        char = match.group()
        if char in _ASCII_SPELLINGS:
            return _ASCII_SPELLINGS[char]
        decomposed = unicodedata.normalize("NFKD", char)
        return SPECIAL.sub("", decomposed) or placeholder

    return SPECIAL.sub(replace, text)


def _plausible(char: str) -> bool:
    """Whether a repaired character is one real text is likely to contain.

    Genuine text such as "CAFÉ…" or the German „Spaß“ can look like mojibake;
    the characters it would "repair" to are rare ones, so those are refused.
    """
    code = ord(char)
    if 0x80 <= code < 0xA0 or 0x700 <= code < 0x800:
        return False
    if 0x180 <= code < 0x370 and not 0x218 <= code <= 0x21B:
        return False
    return unicodedata.category(char) not in ("Cn", "Co", "Cs")


def fix_mojibake(text: str) -> str:
    """Repair UTF-8 text that was read as cp1252 or Latin-1 ("CafÃ©" -> "Café").

    Deliberately cautious: the text is changed only if every special character
    in it is part of a mis-decoded sequence and every repaired character is
    plausible. Anything else is returned untouched.
    """
    for _ in range(3):  # text can be mis-decoded more than once
        if not contains_special_characters(text):
            break
        if any(ord(char) > 0x7F for char in _MOJIBAKE.sub("", text)):
            break
        try:
            repaired = _MOJIBAKE.sub(
                lambda match: bytes(_BYTE_OF[char] for char in match.group()).decode("utf-8"), text
            )
        except UnicodeDecodeError:
            break
        if not all(_plausible(char) for char in repaired if ord(char) > 0x7F):
            break
        # Greek, Cyrillic, Hebrew or Arabic text has many such letters; a lone
        # one is more likely genuine text like "ESPAÑ’" that only looks broken.
        if sum(0x370 <= ord(char) < 0x700 for char in repaired) == 1:
            break
        text = repaired
    return text


def describe_char(char: str) -> str:
    """'U+00E9 LATIN SMALL LETTER E WITH ACUTE (é)' style label for reports."""
    name = unicodedata.name(char, "UNNAMED CHARACTER")
    shown = f" ({char})" if char.isprintable() else ""
    return f"U+{ord(char):04X} {name}{shown}"


def excel_safe(cell: str) -> str:
    """Stop a spreadsheet from running the cell as a formula when opened."""
    if cell.startswith(_FORMULA_STARTS):
        try:
            float(cell)
        except ValueError:
            return "'" + cell
    return cell


@dataclass
class Stats:
    header: list[str] = field(default_factory=list)
    columns: list[str] = field(default_factory=list)
    delimiter: str = ","
    total_rows: int = 0
    matching_rows: int = 0
    rows_written: int = 0
    mojibake_cells: int = 0
    mojibake_example: Optional[tuple[str, str]] = None
    per_column: Counter = field(default_factory=Counter)
    characters: Counter = field(default_factory=Counter)
    examples: list[tuple[int, str, str]] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return self.matching_rows > 0


def _sniff_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=_DELIMITERS).delimiter
    except csv.Error:
        return ","


def _open_reader(path: str, encoding: str, delimiter: Optional[str]) -> tuple[TextIO, Iterator[list[str]], str]:
    try:
        handle = open(path, newline="", encoding=encoding)
    except OSError as exc:
        raise CSVFilterError(f"Cannot open {path}: {exc.strerror}") from exc
    except LookupError as exc:
        raise CSVFilterError(f"Unknown encoding: {encoding}") from exc
    try:
        if delimiter is None:
            delimiter = _sniff_delimiter(handle.read(64 * 1024))
            handle.seek(0)
    except UnicodeDecodeError as exc:
        handle.close()
        raise _encoding_error(path, encoding) from exc
    return handle, csv.reader(handle, delimiter=delimiter), delimiter


def _encoding_error(path: str, encoding: str) -> CSVFilterError:
    return CSVFilterError(
        f"{os.path.basename(path)} is not valid {encoding}. "
        "Files saved by Excel on Windows are usually cp1252: try --encoding cp1252."
    )


def read_header(path: str, encoding: str = "utf-8-sig", delimiter: Optional[str] = None) -> list[str]:
    handle, reader, _ = _open_reader(path, encoding, delimiter)
    with handle:
        try:
            return next(reader, [])
        except UnicodeDecodeError as exc:
            raise _encoding_error(path, encoding) from exc
        except csv.Error as exc:
            raise CSVFilterError(f"Cannot parse {os.path.basename(path)}: {exc}") from exc


def process(
    path: str,
    columns: Optional[Sequence[str]] = None,
    *,
    output: Optional[TextIO] = None,
    mode: str = "filter",
    encoding: str = "utf-8-sig",
    delimiter: Optional[str] = None,
    placeholder: str = "?",
    make_excel_safe: bool = False,
    max_examples: int = 5,
) -> Stats:
    """Scan a CSV and, if output is given, write the result to it.

    mode "filter" writes only the rows that have special characters in the
    chosen columns, unchanged. mode "repair" writes every row, with mojibake
    in the chosen columns repaired and nothing else touched. mode "clean"
    writes every row, with mojibake repaired and then special characters
    replaced by ASCII. columns=None means every column.
    """
    if mode not in ("filter", "repair", "clean"):
        raise ValueError(f"Unknown mode: {mode}")

    handle, reader, delimiter = _open_reader(path, encoding, delimiter)
    stats = Stats(delimiter=delimiter)
    writer = csv.writer(output, delimiter=delimiter, lineterminator="\n") if output else None

    def write(row: Iterable[str]) -> None:
        if writer is None:
            return
        writer.writerow([excel_safe(cell) for cell in row] if make_excel_safe else row)

    with handle:
        try:
            header = next(reader, None)
            if header is None:
                raise CSVFilterError(f"{os.path.basename(path)} is empty.")
            stats.header = header

            if columns:
                missing = [name for name in columns if name not in header]
                if missing:
                    raise CSVFilterError(
                        f"Column not found: {', '.join(missing)}. "
                        f"Available columns: {', '.join(header)}"
                    )
                stats.columns = list(dict.fromkeys(columns))
            else:
                stats.columns = list(dict.fromkeys(header))
            indexes = [header.index(name) for name in stats.columns]

            write(header)
            for row in reader:
                stats.total_rows += 1
                row_matches = False
                for index in indexes:
                    if index >= len(row):
                        continue
                    found = find_special(row[index])
                    if not found:
                        continue
                    row_matches = True
                    stats.per_column[header[index]] += 1
                    stats.characters.update(found)
                    if len(stats.examples) < max_examples:
                        stats.examples.append((reader.line_num, header[index], row[index]))
                    repaired = fix_mojibake(row[index])
                    if repaired != row[index]:
                        stats.mojibake_cells += 1
                        if stats.mojibake_example is None:
                            stats.mojibake_example = (row[index], repaired)
                    if mode == "repair":
                        row[index] = repaired
                    elif mode == "clean":
                        row[index] = to_ascii(repaired, placeholder)
                if row_matches:
                    stats.matching_rows += 1
                if mode != "filter" or row_matches:
                    write(row)
                    stats.rows_written += 1 if writer else 0
        except UnicodeDecodeError as exc:
            raise _encoding_error(path, encoding) from exc
        except csv.Error as exc:
            raise CSVFilterError(
                f"Cannot parse {os.path.basename(path)} near line {reader.line_num}: {exc}"
            ) from exc
    return stats


def format_report(stats: Stats, top: int = 15) -> str:
    lines = [
        f"Size: {stats.total_rows} rows x {len(stats.header)} columns",
        f"Columns checked: {', '.join(stats.columns)}",
    ]
    if not stats.found:
        lines.append("No special characters found.")
        return "\n".join(lines)

    share = stats.matching_rows / stats.total_rows * 100
    lines.append(f"Rows with special characters: {stats.matching_rows} ({share:.1f}%)")
    lines.append("")
    lines.append("By column:")
    for name, count in stats.per_column.most_common():
        lines.append(f"  {name}: {count} rows")
    lines.append("")
    lines.append(f"Characters found ({len(stats.characters)} different):")
    for char, count in stats.characters.most_common(top):
        lines.append(f"  {count:>6} x {describe_char(char)}")
    if len(stats.characters) > top:
        lines.append(f"  ... and {len(stats.characters) - top} more")
    if stats.mojibake_cells:
        before, after = stats.mojibake_example
        lines.append("")
        lines.append(
            f"Mis-decoded text (mojibake): {stats.mojibake_cells} cells, "
            f"e.g. {_shorten(before)!r} should be {_shorten(after)!r}"
        )
    lines.append("")
    lines.append("First examples:")
    for line_num, name, value in stats.examples:
        lines.append(
            f"  line {line_num}, {name}: {_shorten(value)!r} -> {_shorten(to_ascii(fix_mojibake(value)))!r}"
        )
    return "\n".join(lines)


def _shorten(value: str, limit: int = 60) -> str:
    return value if len(value) <= limit else value[: limit - 3] + "..."


def same_file(first: str, second: str) -> bool:
    try:
        return os.path.samefile(first, second)
    except OSError:
        return os.path.abspath(first) == os.path.abspath(second)


def run(
    path: str,
    output_path: Optional[str],
    columns: Optional[Sequence[str]] = None,
    **options,
) -> Stats:
    """process() with the output written to a file path, never over the input."""
    if output_path is None:
        return process(path, columns, **options)
    if same_file(path, output_path):
        raise CSVFilterError("The output file must be different from the input file.")
    # Write beside the target and swap in at the end, so a failed run never
    # leaves a half-written file or destroys an existing one.
    partial = output_path + ".part"
    try:
        with open(partial, "w", newline="", encoding="utf-8") as output:
            stats = process(path, columns, output=output, **options)
        os.replace(partial, output_path)
        return stats
    except OSError as exc:
        raise CSVFilterError(f"Cannot write {output_path}: {exc.strerror}") from exc
    finally:
        if os.path.exists(partial):
            os.remove(partial)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="csvfilter",
        description="Find, report and clean non-ASCII characters in a CSV file.",
        epilog="Exit status: 0 = done, 1 = --check found special characters, 2 = error.",
    )
    parser.add_argument("input", help="CSV file to read")
    parser.add_argument("-o", "--output", help="file to write (use - for standard output)")
    parser.add_argument(
        "-c", "--column", action="append", dest="columns", metavar="NAME",
        help="column to check; repeat for several (default: every column)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--clean", action="store_true",
        help="write every row with special characters replaced by ASCII "
             "(mis-decoded text is repaired first), instead of only the rows that contain them",
    )
    modes.add_argument(
        "--fix-mojibake", action="store_true",
        help="write every row with mis-decoded text repaired (CafÃ© becomes Café) "
             "and everything else, accents included, left as it is",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="report only, and exit with status 1 if special characters are found",
    )
    parser.add_argument("--placeholder", default="?", help="used by --clean when a character has no ASCII spelling (default: ?)")
    parser.add_argument("--encoding", default="utf-8-sig", help="encoding of the input file (default: utf-8)")
    parser.add_argument("--delimiter", help="field separator (default: detected from the file)")
    parser.add_argument(
        "--excel-safe", action="store_true",
        help="prefix cells that start with = + - @ so a spreadsheet does not run them as formulas",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="do not print the report")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.delimiter == "\\t":
        args.delimiter = "\t"
    if args.delimiter is not None and len(args.delimiter) != 1:
        print("csvfilter: --delimiter must be a single character", file=sys.stderr)
        return 2

    options = dict(
        mode="clean" if args.clean else "repair" if args.fix_mojibake else "filter",
        encoding=args.encoding,
        delimiter=args.delimiter,
        placeholder=args.placeholder,
        make_excel_safe=args.excel_safe,
    )
    try:
        if args.output == "-":
            stats = process(args.input, args.columns, output=sys.stdout, **options)
        else:
            stats = run(args.input, None if args.check else args.output, args.columns, **options)
    except CSVFilterError as exc:
        print(f"csvfilter: {exc}", file=sys.stderr)
        return 2

    if not args.quiet:
        print(format_report(stats), file=sys.stderr)
        if stats.rows_written and args.output not in (None, "-"):
            print(f"\nWrote {stats.rows_written} rows to {args.output}", file=sys.stderr)
    return 1 if args.check and stats.found else 0


if __name__ == "__main__":
    sys.exit(main())
