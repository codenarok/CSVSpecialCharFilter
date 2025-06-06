import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import re
from typing import Union

class CSVFilterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CSV Special Character Filter")
        self._configure_window()
        self._create_widgets()

    def _configure_window(self):
        # Configure window size and position
        window_width = 450
        window_height = 320 # Increased window height
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
            "• Robust error handling\n\n"
            "Click 'Start Processing' to begin."
        )
        description_label = tk.Label(
            self.root,
            text=description_text,
            font=("Arial", 11),
            bg='#f0f0f0',
            fg='#555555',
            wraplength=410,
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
        exit_button.pack(side=tk.LEFT, padx=20, ipady=5) # Increased spacing & internal y-padding

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

    @staticmethod
    def select_file(title: str) -> str:
        """
        Open a file dialog to select a CSV file.
        
        Args:
            title: The title for the file dialog
            
        Returns:
            str: The selected file path, or empty string if cancelled
        """
        # Create a temporary root for the dialog if one isn't readily available
        # or ensure the main root isn't destroyed prematurely.
        # For simplicity, we'll create a new Toplevel, then withdraw and destroy it.
        dialog_root = tk.Toplevel()
        dialog_root.withdraw()  # Hide the Toplevel window
        file_path = filedialog.askopenfilename(
            parent=dialog_root, # Associate dialog with a temporary window
            title=title, 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        dialog_root.destroy()
        return file_path

    @staticmethod
    def save_file_as(title: str) -> str:
        """
        Open a file dialog to save a CSV file.
        
        Args:
            title: The title for the file dialog
            
        Returns:
            str: The selected file path, or empty string if cancelled
        """
        dialog_root = tk.Toplevel()
        dialog_root.withdraw()
        file_path = filedialog.asksaveasfilename(
            parent=dialog_root,
            title=title, 
            defaultextension=".csv", 
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        dialog_root.destroy()
        return file_path

    def run_csv_processing(self) -> None:
        """
        The main CSV processing logic.
        """
        # Select input file
        input_csv_path = self.select_file("Select the input CSV file")
        if not input_csv_path:
            messagebox.showinfo("Cancelled", "No input file selected. Operation cancelled.", parent=self.root)
            return

        # Read and validate CSV file
        try:
            df = pd.read_csv(input_csv_path)
            
            # Check if file is empty
            if df.empty:
                messagebox.showerror("Error", "The selected CSV file is empty.", parent=self.root)
                return
                
        except FileNotFoundError:
            messagebox.showerror("Error", f"Input file not found:\n{input_csv_path}", parent=self.root)
            return
        except pd.errors.EmptyDataError:
            messagebox.showerror("Error", "The selected file appears to be empty or corrupted.", parent=self.root)
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error reading CSV file:\n{str(e)}", parent=self.root)
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
            return

        # Filter rows where 'Title' or 'Developer' contains special characters
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
            messagebox.showerror("Error", f"Error processing data:\n{str(e)}", parent=self.root)
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
            return

        # Select output file
        output_csv_path = self.save_file_as("Save the filtered CSV file as")
        if not output_csv_path:
            messagebox.showinfo("Cancelled", "No output location selected. Operation cancelled.", parent=self.root)
            return

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
        except Exception as e:
            messagebox.showerror("Error", f"Error saving filtered CSV file:\n{str(e)}", parent=self.root)

def main() -> None:
    """
    Create and run the main GUI application.
    """
    root = tk.Tk()
    app = CSVFilterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

