import pandas as pd
import tkinter as tk
from tkinter import filedialog
import re

def contains_special_characters(text):
    # Define the pattern for characters outside the standard printable ASCII range (space to ~)
    # This aims to catch characters often problematic for basic VARCHAR fields
    pattern = r'[^\x20-\x7E]' # Match characters NOT in the range \x20 (space) to \x7E (~)
    return bool(re.search(pattern, str(text)))

def select_file(title):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(title=title, filetypes=[("CSV files", "*.csv")])
    return file_path

def save_file_as(title):
    root = tk.Tk()
    root.withdraw() # Hide the main window
    file_path = filedialog.asksaveasfilename(title=title, defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    return file_path

def main():
    input_csv_path = select_file("Select the input CSV file")
    if not input_csv_path:
        print("No input file selected. Exiting.")
        return

    try:
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv_path}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Check if 'Title' and 'Developer' columns exist
    if 'Title' not in df.columns or 'Developer' not in df.columns:
        print("Error: CSV must contain 'Title' and 'Developer' columns.")
        return

    # Filter rows where 'Title' or 'Developer' contains special characters
    filtered_df = df[df.apply(lambda row: contains_special_characters(row['Title']) or contains_special_characters(row['Developer']), axis=1)]

    if filtered_df.empty:
        print("No rows found with special characters in 'Title' or 'Developer' columns.")
        return

    output_csv_path = save_file_as("Save the filtered CSV file as")
    if not output_csv_path:
        print("No output file location selected. Exiting.")
        return

    try:
        filtered_df.to_csv(output_csv_path, index=False)
        print(f"Filtered data saved to {output_csv_path}")
    except Exception as e:
        print(f"Error saving filtered CSV file: {e}")

if __name__ == "__main__":
    main()

