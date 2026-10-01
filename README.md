# CSV Special Character Filter

Find, report and clean the characters in a CSV file that break imports into systems expecting plain ASCII, such as SQL `VARCHAR` columns, legacy ERPs and fixed-width exports.

A "special character" is anything outside printable ASCII (space to `~`) plus tab and line breaks: accented letters, typographic quotes and dashes, non-breaking spaces, emoji and control characters.

- **No dependencies.** Python 3.9+ standard library only.
- **Works offline.** Your data never leaves your machine.
- **Large files are fine.** Rows are read one at a time.

## What it does

| Mode | Result |
| --- | --- |
| Report | Shows how many rows are affected, which columns, and exactly which characters (with their Unicode names). |
| Filter | Saves only the rows that contain special characters, unchanged, so you can review them. |
| Clean | Saves every row with special characters replaced by plain ASCII: `Café` becomes `Cafe`, `“quoted”` becomes `"quoted"`, `Şeker` becomes `Seker`. |

## Command line

```bash
git clone https://github.com/codenarok/CSVSpecialCharFilter.git
cd CSVSpecialCharFilter
```

Report on every column:

```bash
python3 csvfilter.py games.csv
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
python3 csvfilter.py games.csv -c Title -c Developer -o needs_review.csv
```

Save a cleaned copy of the whole file:

```bash
python3 csvfilter.py games.csv --clean -o games_ascii.csv
```

Use it as a gate in a script or pipeline (exit status 1 if anything is found):

```bash
python3 csvfilter.py games.csv --check
```

### Options

| Option | Meaning |
| --- | --- |
| `-o FILE` | File to write. `-` writes to standard output. |
| `-c NAME` | Column to check. Repeat for several. Default: every column. |
| `--clean` | Write every row, cleaned, instead of only the affected rows. |
| `--check` | Report only. Exit status 1 if special characters are found. |
| `--placeholder TEXT` | Used by `--clean` for characters with no ASCII spelling, such as emoji. Default `?`. |
| `--encoding NAME` | Encoding of the input. Default UTF-8. Excel on Windows often saves `cp1252`. |
| `--delimiter CHAR` | Field separator. Default: detected (`,` `;` tab or `\|`). |
| `--excel-safe` | Neutralise cells that start with `=`, `+`, `-` or `@` (see Safety). |
| `-q` | Do not print the report. |

## Desktop window

```bash
python3 main.py
```

Open a CSV, select the columns to check (none selected means all), then **Scan**, **Save matching rows** or **Save cleaned copy**. Needs Tkinter, which ships with most Python installs.

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
