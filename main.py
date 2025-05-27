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

def run_csv_processing(welcome_window):
    """The main CSV processing logic, initiated after the welcome screen."""
    welcome_window.destroy() # Close the welcome screen

    input_csv_path = select_file("Select the input CSV file")
    if not input_csv_path:
        print("No input file selected. Exiting program.")
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
        print("Output file location is not selected. Exiting program.")
        return

    try:
        filtered_df.to_csv(output_csv_path, index=False)
        print(f"Filtered data saved to {output_csv_path}")
    except Exception as e:
        print(f"Error saving filtered CSV file: {e}")

def main():
    # Create the main application window for the welcome screen
    welcome_root = tk.Tk()
    welcome_root.title("CSV Special Character Filter")

    # Configure window size and position
    window_width = 400
    window_height = 250
    screen_width = welcome_root.winfo_screenwidth()
    screen_height = welcome_root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    welcome_root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

    welcome_root.configure(bg='#f0f0f0')

    # Main title label
    title_label = tk.Label(
        welcome_root,
        text="Welcome to the CSV Filter Tool!",
        font=("Arial", 16, "bold"),
        bg='#f0f0f0',
        fg='#333333',
        pady=20
    )
    title_label.pack(fill=tk.X)

    # Description label
    description_text = (
        "This tool identifies rows in a CSV file where 'Title' or 'Developer' "
        "columns contain special (non-ASCII) characters. "
        "Click 'Start Processing' to select your CSV and save the filtered results."
    )
    description_label = tk.Label(
        welcome_root,
        text=description_text,
        font=("Arial", 10),
        bg='#f0f0f0',
        fg='#555555',
        wraplength=window_width - 40,
        justify=tk.CENTER,
        pady=10
    )
    description_label.pack(fill=tk.X, padx=20)

    # Frame for buttons
    button_frame = tk.Frame(welcome_root, bg='#f0f0f0')
    button_frame.pack(pady=20, expand=True)

    # Start button
    start_button = tk.Button(
        button_frame,
        text="Start Processing",
        font=("Arial", 10, "bold"), # Reduced font size
        command=lambda: run_csv_processing(welcome_root),
        relief=tk.RAISED,
        bd=2,
        padx=10, # Reduced padding
        pady=5   # Reduced padding
    )
    start_button.pack(side=tk.LEFT, padx=10) # Reduced padx

    # Exit button
    exit_button = tk.Button(
        button_frame,
        text="Exit",
        font=("Arial", 10, "bold"), # Reduced font size
        bg="#f44336",
        fg="white",
        command=welcome_root.destroy,
        relief=tk.RAISED,
        bd=2,
        padx=10, # Reduced padding
        pady=5   # Reduced padding
    )
    exit_button.pack(side=tk.LEFT, padx=10) # Reduced padx

    welcome_root.resizable(False, False)
    welcome_root.mainloop()

if __name__ == "__main__":
    main()

