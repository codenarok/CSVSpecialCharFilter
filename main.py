import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import re
from typing import Union
import os

# Tooltip class for providing hover text on widgets
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True) # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=2, ipady=2)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class CSVFilterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CSV Special Character Filter")
        self.status_var = tk.StringVar() # For status bar
        self._configure_window()
        self._create_widgets()
        self.status_var.set("Ready") # Initial status

    def _configure_window(self):
        # Configure window size and position
        window_width = 900 # Increased window width
        window_height = 640 # Increased window height
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(False, False)

    def _create_widgets(self):
        # Main title label
        title_label = tk.Label(
            self.root,
            text="Welcome to the CSV Filter Tool!",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0',
            fg='#333333',
            pady=20 # Adjusted padding
        )
        title_label.pack(fill=tk.X, padx=20) # Added padx for title

        # Description label
        description_text = (
            "This tool identifies rows in a CSV file where 'Title' or 'Developer' "
            "columns contain special (non-ASCII) characters.\n\n"
            "Features:\n"
            "• GUI-based file selection (Buttons are improved)\n"
            "• Detailed processing statistics\n"
            "• Robust error handling\n"
            "• Calculate and display CSV dimensions (rows x columns)\n\n"
            "Click 'Start Processing' to begin or 'Calculate Dimensions' for file insights."
        )
        description_label = tk.Label(
            self.root,
            text=description_text,
            font=("Arial", 11),
            bg='#f0f0f0',
            fg='#555555',
            wraplength=850, # Adjusted wraplength for wider window
            justify=tk.LEFT,
            pady=10 # Adjusted padding
        )
        description_label.pack(fill=tk.X, padx=20)

        # Frame for buttons
        button_frame = tk.Frame(self.root, bg='#f0f0f0')
        button_frame.pack(pady=20, expand=True) # Adjusted padding

        # Common button styling
        button_font = ("Arial", 12, "bold")
        button_relief = tk.RAISED # Changed back to RAISED for visibility
        button_border_width = 2 # Explicitly set border width
        button_padx = 25 # Increased horizontal padding
        button_pady = 12 # Increased vertical padding

        # Start button
        start_button = tk.Button(
            button_frame,
            text="Start Processing",
            font=button_font,
            bg="#4CAF50", # Green
            fg="white",
            command=self.run_csv_processing,
            relief=button_relief,
            bd=button_border_width,
            padx=button_padx,
            pady=button_pady,
            cursor="hand2",
            activebackground="#45a049", # Darker green on click
            activeforeground="white"
        )
        start_button.pack(side=tk.LEFT, padx=20, ipady=5) # Increased spacing & internal y-padding
        Tooltip(start_button, "Process selected CSV for special characters in 'Title' and 'Developer' columns.")

        # Calculate Dimensions Button
        calc_dims_button = tk.Button(
            button_frame,
            text="Calculate Dimensions",
            font=button_font,
            bg="#2196F3",  # Blue
            fg="white",
            command=self.calculate_and_display_dimensions,
            relief=button_relief,
            bd=button_border_width,
            padx=button_padx,
            pady=button_pady,
            cursor="hand2",
            activebackground="#1E88E5",  # Darker blue
            activeforeground="white"
        )
        calc_dims_button.pack(side=tk.LEFT, padx=20, ipady=5)
        Tooltip(calc_dims_button, "Calculate and display the number of rows and columns for a selected CSV file.")

        # Exit button
        exit_button = tk.Button(
            button_frame,
            text="Exit",
            font=button_font,
            bg="#f44336", # Red
            fg="white",
            command=self.root.destroy,
            relief=button_relief,
            bd=button_border_width,
            padx=button_padx,
            pady=button_pady,
            cursor="hand2",
            activebackground="#e53935", # Darker red on click
            activeforeground="white"
        )
        exit_button.pack(side=tk.LEFT, padx=10, ipady=5) # Adjusted padx & internal y-padding
        Tooltip(exit_button, "Close the application.")

        # Status Bar
        status_label = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W, 
            font=("Arial", 9),
            bg='#dfdfdf', 
            fg='#333333',
            padx=5
        )
        status_label.pack(side=tk.BOTTOM, fill=tk.X, ipady=3)

    @staticmethod
    def contains_special_characters(text: Union[str, float, None]) -> bool:
        """
        Check if text contains special characters outside printable ASCII range.
        
        Args:
            text: The text to check (can be string, float, or None)
            
        Returns:
            bool: True if special characters are found, False otherwise
        """
        # Handle NaN, None, or empty values
        if pd.isna(text) or text is None:
            return False
        
        # Convert to string to handle numeric values
        text_str = str(text)
        # Define the pattern for characters outside the standard printable ASCII range
        # Include common whitespace characters (tab, newline) as valid ASCII
        # This aims to catch characters often problematic for basic VARCHAR fields
        pattern = r'[^\\x09\\x0A\\x0D\\x20-\\x7E]'  # Match characters NOT in valid ASCII range
        # \\x09 = tab, \\x0A = newline, \\x0D = carriage return, \\x20-\\x7E = printable ASCII
        return bool(re.search(pattern, text_str))

    # Removed @staticmethod, now an instance method
    def select_file(self, title: str) -> str:
        """
        Open a file dialog to select a CSV file.
        
        Args:
            title: The title for the file dialog
            
        Returns:
            str: The selected file path, or empty string if cancelled
        """
        file_path = filedialog.askopenfilename(
            parent=self.root, # Parented to the main root window
            title=title, 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        # dialog_root.destroy() # No longer needed
        return file_path

    # Removed @staticmethod, now an instance method
    def save_file_as(self, title: str) -> str:
        """
        Open a file dialog to save a CSV file.
        
        Args:
            title: The title for the file dialog
            
        Returns:
            str: The selected file path, or empty string if cancelled
        """
        file_path = filedialog.asksaveasfilename(
            parent=self.root, # Parented to the main root window
            title=title, 
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        # dialog_root.destroy() # No longer needed
        return file_path

    def calculate_and_display_dimensions(self) -> None:
        """
        Prompts the user to select a CSV file, then calculates and displays its dimensions (rows x columns).
        """
        self.status_var.set("Awaiting CSV file selection for dimension calculation...")
        input_csv_path = self.select_file("Select a CSV file to calculate dimensions") # Now self.select_file
        if not input_csv_path:
            messagebox.showinfo("Cancelled", "No file selected. Operation cancelled.", parent=self.root)
            self.status_var.set("Dimension calculation cancelled by user.")
            return
        
        self.status_var.set(f"Calculating dimensions for: {os.path.basename(input_csv_path)}")
        try:
            df = pd.read_csv(input_csv_path)
            
            rows, cols = df.shape
            
            if df.empty:
                # This handles files with headers but no data rows (shape will be (0, num_cols))
                # or files that are empty but pandas could still determine columns (less common for read_csv)
                messagebox.showinfo(
                    "CSV Dimensions",
                    f"The selected CSV file has 0 data rows.\n\nRows: {rows}\nColumns: {cols}",
                    parent=self.root
                )
                self.status_var.set(f"Dimensions calculated for {os.path.basename(input_csv_path)}: {rows} rows, {cols} columns.")
            else:
                messagebox.showinfo(
                    "CSV Dimensions",
                    f"The selected CSV file has:\\n\\nRows: {rows}\\nColumns: {cols}",
                    parent=self.root
                )
                self.status_var.set(f"Dimensions calculated for {os.path.basename(input_csv_path)}: {rows} rows, {cols} columns.")
                
        except FileNotFoundError:
            messagebox.showerror("Error", f"File not found:\\n{input_csv_path}", parent=self.root)
            self.status_var.set(f"Error: File not found - {os.path.basename(input_csv_path)}")
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", "The selected file is completely empty or not a valid CSV.", parent=self.root)
            self.status_var.set("Error: Selected file is empty or not a valid CSV.")
        except pd.errors.ParserError:
            messagebox.showerror("Error", "Could not parse the CSV file. Please ensure it's a valid CSV format.", parent=self.root)
            self.status_var.set("Error: Could not parse the CSV file.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while reading or processing the CSV file:\\n{str(e)}", parent=self.root)
            self.status_var.set(f"Error calculating dimensions: {str(e)}")

    def run_csv_processing(self) -> None:
        """
        The main CSV processing logic.
        """
        self.status_var.set("Awaiting input CSV file selection for processing...")
        # Select input file
        input_csv_path = self.select_file("Select the input CSV file") # Now self.select_file
        if not input_csv_path:
            messagebox.showinfo("Cancelled", "No input file selected. Operation cancelled.", parent=self.root)
            self.status_var.set("CSV processing cancelled: No input file selected.")
            return
        
        self.status_var.set(f"Processing input file: {os.path.basename(input_csv_path)}")

        # Read and validate CSV file
        try:
            df = pd.read_csv(input_csv_path)
            
            # Check if file is empty
            if df.empty:
                messagebox.showerror("Error", "The selected CSV file is empty.", parent=self.root)
                self.status_var.set(f"Error: Input CSV file '{os.path.basename(input_csv_path)}' is empty.")
                return
                
        except FileNotFoundError:
            messagebox.showerror("Error", f"Input file not found:\\n{input_csv_path}", parent=self.root)
            self.status_var.set(f"Error: Input file not found - {os.path.basename(input_csv_path)}")
            return
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", "The selected file appears to be empty or corrupted.", parent=self.root)
            self.status_var.set(f"Error: Input file '{os.path.basename(input_csv_path)}' is empty or corrupted.")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file:\\n{str(e)}", parent=self.root)
            self.status_var.set(f"Error reading CSV '{os.path.basename(input_csv_path)}': {str(e)}")
            return

        # Check if required columns exist
        required_columns = ['Title', 'Developer']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            messagebox.showerror(
                "Missing Columns", 
                f"CSV must contain the following columns:\n{', '.join(required_columns)}\n\n"
                f"Missing: {', '.join(missing_columns)}\n\n"
                f"Available columns: {', '.join(df.columns.tolist())}",
                parent=self.root
            )
            self.status_var.set(f"Error: Missing required columns in '{os.path.basename(input_csv_path)}'.")
            return

        # Filter rows where 'Title' or 'Developer' contains special characters
        self.status_var.set(f"Filtering data in '{os.path.basename(input_csv_path)}'...")
        try:
            # Use the static method for character checking
            filtered_df = df[
                df.apply(
                    lambda row: (
                        self.contains_special_characters(row.get('Title')) or 
                        self.contains_special_characters(row.get('Developer'))
                    ), 
                    axis=1
                )
            ]
        except Exception as e:
            messagebox.showerror("Error", f"Error processing data:\\n{str(e)}", parent=self.root)
            self.status_var.set(f"Error processing data in '{os.path.basename(input_csv_path)}': {str(e)}")
            return

        # Show processing results
        total_rows = len(df)
        filtered_rows = len(filtered_df)
        
        if filtered_df.empty:
            messagebox.showinfo(
                "No Special Characters Found", 
                f"Processed {total_rows} rows.\n\n"
                "No rows found with special characters in 'Title' or 'Developer' columns.",
                parent=self.root
            )
            self.status_var.set(f"Processing complete for '{os.path.basename(input_csv_path)}'. No special characters found.")
            return

        # Ask user if they want to proceed with saving
        result = messagebox.askyesno(
            "Special Characters Found", 
            f"Processing Results:\n"
            f"• Total rows processed: {total_rows}\n"
            f"• Rows with special characters: {filtered_rows}\n"
            f"• Percentage: {(filtered_rows/total_rows)*100:.1f}%\n\n"
            f"Do you want to save the filtered results?",
            parent=self.root
        )
        
        if not result:
            messagebox.showinfo("Cancelled", "Operation cancelled by user.", parent=self.root)
            self.status_var.set("Save operation cancelled by user.")
            return

        self.status_var.set("Awaiting output file location selection...")
        # Select output file
        output_csv_path = self.save_file_as("Save the filtered CSV file as") # Now self.save_file_as
        if not output_csv_path:
            messagebox.showinfo("Cancelled", "No output location selected. Operation cancelled.", parent=self.root)
            self.status_var.set("Save operation cancelled: No output location selected.")
            return
        
        self.status_var.set(f"Saving filtered data to: {os.path.basename(output_csv_path)}")

        # Save filtered data
        try:
            filtered_df.to_csv(output_csv_path, index=False)
            messagebox.showinfo(
                "Success", 
                f"Filtered data successfully saved!\n\n"
                f"Location: {output_csv_path}\n"
                f"Rows saved: {filtered_rows}",
                parent=self.root
            )
            self.status_var.set(f"Filtered data saved successfully to '{os.path.basename(output_csv_path)}'.")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving filtered CSV file:\\n{str(e)}", parent=self.root)
            self.status_var.set(f"Error saving filtered data to '{os.path.basename(output_csv_path)}': {str(e)}")

def main() -> None:
    """
    Create and run the main GUI application.
    """
    root = tk.Tk()
    app = CSVFilterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

