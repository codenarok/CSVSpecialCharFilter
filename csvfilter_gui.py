"""Desktop window for csvfilter. Run: python csvfilter_gui.py"""
from __future__ import annotations

import os
import sys
from typing import Optional

import csvfilter

# Some Pythons (Homebrew's, minimal Linux installs) ship without Tkinter.
# Keep the module importable so main() can explain, instead of a traceback.
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    tk = None

_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"
NO_TKINTER = f"""csvfilter-gui needs Tkinter, which this Python ({_VERSION}) does not include.

To add it:
  Homebrew (macOS):   brew install python-tk@{_VERSION}
  Debian / Ubuntu:    sudo apt install python3-tk
  Fedora:             sudo dnf install python3-tkinter

The command-line tool does not need it: csvfilter --help"""

ENCODINGS = {
    "UTF-8 (most files)": "utf-8-sig",
    "Windows / Excel (cp1252)": "cp1252",
    "Latin-1": "latin-1",
}
ALLOWED = {"ASCII only": ""}
for _name, _description in csvfilter.ALLOW_DESCRIPTIONS.items():
    _label = _description.replace("everything ", "").replace(" can store", "")
    ALLOWED[f"ASCII + {_label}"] = csvfilter.ALLOW_SETS[_name]
CSV_TYPES = [("CSV files", "*.csv"), ("All files", "*.*")]


class CSVFilterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CSV Special Character Filter")
        self.root.minsize(720, 520)
        self.input_path: Optional[str] = None
        self.status_var = tk.StringVar(value="Open a CSV file to begin.")
        self.encoding_var = tk.StringVar(value=next(iter(ENCODINGS)))
        self.allowed_var = tk.StringVar(value=next(iter(ALLOWED)))
        self.excel_safe_var = tk.BooleanVar(value=False)
        self._create_widgets()

    def _create_widgets(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(2, weight=1)

        top = ttk.Frame(outer)
        top.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Button(top, text="Open CSV...", command=self.open_file).pack(side=tk.LEFT)
        ttk.Label(top, text="Encoding:").pack(side=tk.LEFT, padx=(16, 4))
        encoding_box = ttk.Combobox(
            top, textvariable=self.encoding_var, values=list(ENCODINGS), state="readonly", width=24
        )
        encoding_box.pack(side=tk.LEFT)
        encoding_box.bind("<<ComboboxSelected>>", lambda _event: self._load_header())
        ttk.Label(top, text="Allow:").pack(side=tk.LEFT, padx=(16, 4))
        ttk.Combobox(
            top, textvariable=self.allowed_var, values=list(ALLOWED), state="readonly", width=34, height=len(ALLOWED)
        ).pack(side=tk.LEFT)

        ttk.Label(outer, text="Columns to check").grid(row=1, column=0, sticky="w")
        ttk.Label(outer, text="Report").grid(row=1, column=1, sticky="w", padx=(12, 0))

        # The same thin outline on both panes; by default the report has none.
        outline = dict(
            relief=tk.FLAT, borderwidth=0, highlightthickness=1,
            highlightbackground="#b0b0b0", highlightcolor="#b0b0b0",
        )
        self.column_list = tk.Listbox(outer, selectmode=tk.EXTENDED, exportselection=False, width=28, **outline)
        self.column_list.grid(row=2, column=0, sticky="nsew")

        self.report = tk.Text(outer, wrap="word", state=tk.DISABLED, height=18, padx=6, pady=4, **outline)
        self.report.grid(row=2, column=1, sticky="nsew", padx=(12, 0))

        ttk.Checkbutton(
            outer,
            text="Make saved files safe to open in Excel (neutralise cells starting with = + - @)",
            variable=self.excel_safe_var,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        actions = ttk.Frame(outer)
        actions.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.action_buttons = [
            ttk.Button(actions, text="Scan", command=self.scan),
            ttk.Button(actions, text="Save matching rows...", command=lambda: self.save("filter")),
            ttk.Button(actions, text="Save repaired copy...", command=lambda: self.save("repair")),
            ttk.Button(actions, text="Save cleaned copy...", command=lambda: self.save("clean")),
        ]
        for button in self.action_buttons:
            button.pack(side=tk.LEFT, padx=(0, 8))
            button.state(["disabled"])

        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=(6, 2)).pack(
            side=tk.BOTTOM, fill=tk.X
        )

    # --- helpers ---

    def _encoding(self) -> str:
        return ENCODINGS[self.encoding_var.get()]

    def _selected_columns(self) -> Optional[list[str]]:
        """Chosen column names, or None (meaning all) when nothing is selected."""
        chosen = [self.column_list.get(index) for index in self.column_list.curselection()]
        return chosen or None

    def _show_report(self, text: str) -> None:
        self.report.configure(state=tk.NORMAL)
        self.report.delete("1.0", tk.END)
        self.report.insert("1.0", text)
        self.report.configure(state=tk.DISABLED)

    def _fail(self, error: Exception) -> None:
        self.status_var.set("Something went wrong. See the message.")
        messagebox.showerror("CSV Special Character Filter", str(error), parent=self.root)

    def _load_header(self) -> bool:
        if not self.input_path:
            return False
        try:
            header = csvfilter.read_header(self.input_path, self._encoding())
        except csvfilter.CSVFilterError as error:
            self._fail(error)
            return False
        self.column_list.delete(0, tk.END)
        for name in dict.fromkeys(header):
            self.column_list.insert(tk.END, name)
        return True

    # --- actions ---

    def open_file(self) -> None:
        path = filedialog.askopenfilename(parent=self.root, title="Open a CSV file", filetypes=CSV_TYPES)
        if not path:
            return
        self.load(path)

    def load(self, path: str) -> None:
        self.input_path = path
        self._show_report("")
        loaded = self._load_header()
        for button in self.action_buttons:
            button.state(["!disabled"] if loaded else ["disabled"])
        if loaded:
            self.status_var.set(
                f"{os.path.basename(path)} opened. Select columns (none selected = all), then Scan."
            )

    def scan(self) -> None:
        self._run(output_path=None, mode="filter")

    def save(self, mode: str) -> None:
        if not self.input_path:
            return
        stem, _ = os.path.splitext(os.path.basename(self.input_path))
        suffix = {"clean": "cleaned", "repair": "repaired", "filter": "special_chars"}[mode]
        output_path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save as",
            initialfile=f"{stem}_{suffix}.csv",
            defaultextension=".csv",
            filetypes=CSV_TYPES,
        )
        if output_path:
            self._run(output_path=output_path, mode=mode)

    def _run(self, output_path: Optional[str], mode: str) -> None:
        if not self.input_path:
            return
        self.status_var.set("Working...")
        self.root.update_idletasks()
        try:
            stats = csvfilter.run(
                self.input_path,
                output_path,
                self._selected_columns(),
                mode=mode,
                encoding=self._encoding(),
                allowed=ALLOWED[self.allowed_var.get()],
                make_excel_safe=self.excel_safe_var.get(),
            )
        except csvfilter.CSVFilterError as error:
            self._fail(error)
            return
        self._show_report(csvfilter.format_report(stats))
        if output_path:
            self.status_var.set(f"Saved {stats.rows_written} rows to {os.path.basename(output_path)}.")
        elif stats.found:
            self.status_var.set(f"{stats.matching_rows} of {stats.total_rows} rows have special characters.")
        else:
            self.status_var.set(f"No special characters in {stats.total_rows} rows.")


def main() -> int:
    if tk is None:
        print(NO_TKINTER, file=sys.stderr)
        return 1
    root = tk.Tk()
    CSVFilterApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
