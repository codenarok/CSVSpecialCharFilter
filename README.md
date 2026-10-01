# CSV Special Character Filter

Find, report, repair and clean the characters in a CSV file that break imports into systems expecting plain ASCII, such as SQL `VARCHAR` columns, legacy ERPs and fixed-width exports.

A "special character" is anything outside printable ASCII (space to `~`) plus tab and line breaks: accented letters, typographic quotes and dashes, non-breaking spaces, emoji and control characters.

- **Any CSV file.** Every column is checked by default, whatever it is called; you can narrow it to the columns you name.
- **No dependencies.** Python 3.9+ standard library only.
- **Works offline.** Your data never leaves your machine.
- **Large files are fine.** Rows are read one at a time.

## What it does

| Mode | Result |
| --- | --- |
| Report | Shows how many rows are affected, which columns, and exactly which characters (with their Unicode names). |
| Filter | Saves only the rows that contain special characters, unchanged, so you can review them. |
| Repair | Saves every row with mis-decoded text (mojibake) put right: `CafÃ©` becomes `Café`, `itâ€™s` becomes `it’s`. Accents are kept. |
| Clean | Saves every row with special characters replaced by plain ASCII: `Café` becomes `Cafe`, `“quoted”` becomes `"quoted"`, `Şeker` becomes `Seker`. Mis-decoded text is repaired first, so `CafÃ©` also becomes `Cafe`. |

## Which files work

- **Columns:** any names and any number. Nothing is tied to particular columns such as `Title` or `Developer`.
- **Separators:** comma, semicolon, tab and pipe are detected, so `.tsv` files and semicolon-separated exports work. `--delimiter` overrides the guess.
- **Encoding:** UTF-8 by default. For files saved by Excel on Windows, use `--encoding cp1252`.
- **Header row:** the first row must hold the column names, because columns are chosen by name. In a file with no header, the first data row is taken as the names and is not checked.

## Install

With [pipx](https://pipx.pypa.io), which gives you a `csvfilter` command without touching your other Python packages:

```bash
pipx install git+https://github.com/codenarok/CSVSpecialCharFilter.git
```

Plain `pip install git+https://github.com/codenarok/CSVSpecialCharFilter.git` works too. Or skip installing: clone the repository and run `python3 csvfilter.py` in place of `csvfilter` below.

## Command line

Report on every column:

```bash
csvfilter games.csv
```

```text
Size: 3 rows x 3 columns
Columns checked: Title, Developer, Price
Rows with special characters: 2 (66.7%)

By column:
  Title: 1 rows
  Developer: 1 rows

Characters found (5 different):
       1 x U+00E9 LATIN SMALL LETTER E WITH ACUTE (é)
       1 x U+015E LATIN CAPITAL LETTER S WITH CEDILLA (Ş)
       ...

First examples:
  line 3, Title: 'Café Adventure' -> 'Cafe Adventure'
```

Save the affected rows, checking two columns only:

```bash
csvfilter games.csv -c Title -c Developer -o needs_review.csv
```

Save a cleaned copy of the whole file:

```bash
csvfilter games.csv --clean -o games_ascii.csv
```

Repair mis-decoded text and keep everything else as it is:

```bash
csvfilter games.csv --fix-mojibake -o games_repaired.csv
```

Use it as a gate in a script or pipeline (exit status 1 if anything is found):

```bash
csvfilter games.csv --check
```

### Options

| Option | Meaning |
| --- | --- |
| `-o FILE` | File to write. `-` writes to standard output. |
| `-c NAME` | Column to check. Repeat for several. Default: every column. |
| `--clean` | Write every row, cleaned to ASCII, instead of only the affected rows. |
| `--fix-mojibake` | Write every row with mis-decoded text repaired. Cannot be combined with `--clean`, which already includes it. |
| `--check` | Report only. Exit status 1 if special characters are found. |
| `--placeholder TEXT` | Used by `--clean` for characters with no ASCII spelling, such as emoji. Default `?`. |
| `--encoding NAME` | Encoding of the input. Default UTF-8. Excel on Windows often saves `cp1252`. |
| `--delimiter CHAR` | Field separator. Default: detected (`,` `;` tab or `\|`). |
| `--excel-safe` | Neutralise cells that start with `=`, `+`, `-` or `@` (see Safety). |
| `-q` | Do not print the report. |

### Mis-decoded text (mojibake)

When a UTF-8 file is opened as Windows-1252 or Latin-1 somewhere along the way, `Café` turns into `CafÃ©` and `it’s` into `itâ€™s`. The report counts cells that look like this, and `--fix-mojibake` and `--clean` repair them, including text garbled twice.

The repair is deliberately cautious. A cell is changed only if every special character in it is part of a mis-decoded sequence and the result is plausible, so genuine text such as `„Spaß“` or `CAFÉ…` is left alone. The cost is that a cell mixing correct and garbled text is not repaired.

## Desktop window

```bash
csvfilter-gui
```

(or `python3 csvfilter_gui.py` from a clone). Open a CSV, select the columns to check (none selected means all), then **Scan**, **Save matching rows**, **Save repaired copy** or **Save cleaned copy**.

The window needs Tkinter. The Python that comes with macOS, Windows installers and Anaconda includes it. Homebrew's Python does not, so if `csvfilter-gui` stops with `No module named '_tkinter'`, add it with `brew install python-tk@3.14` (match the number to your Python version). On Debian or Ubuntu it is `sudo apt install python3-tk`. The command-line `csvfilter` never needs it.

## Safety

- The input file is never modified, and the tool refuses to write its output over the input.
- Output is written to a temporary `.part` file and moved into place only when the run succeeds, so a failed run cannot damage an existing file.
- CSV files from untrusted sources can contain cells such as `=HYPERLINK(...)` that a spreadsheet runs as formulas when the file is opened. `--excel-safe` prefixes those cells with `'` so they are shown as text. Plain numbers such as `-5.5` are left alone.
- `.gitignore` excludes `*.csv` so real data is not committed to this public repository by accident.

## Tests

```bash
python3 -m unittest discover -s tests
```

## Licence

MIT. See [LICENSE](LICENSE).
