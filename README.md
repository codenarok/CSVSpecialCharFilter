# CSV Special Character Filter

This Python script helps filter a CSV file to find rows where specific columns ('Title' and 'Developer' by default) contain special characters. It defines "special characters" as those outside the standard printable ASCII range (space to `~`), which often cause issues when importing data into systems like SQL databases with basic `VARCHAR` fields.

## Features

*   Uses a graphical file dialog (Tkinter) to select the input CSV file.
*   Uses a graphical file dialog to specify the output CSV file path.
*   Reads the CSV using the `pandas` library.
*   Filters rows based on the presence of non-standard ASCII characters in the 'Title' or 'Developer' columns.
*   Saves the filtered data to a new CSV file.
*   Calculates and displays the dimensions (rows x columns) of a selected CSV file.
*   Object-oriented design for better maintainability.
*   Improved UI styling for better visibility and user experience.
*   Provides detailed summary statistics after processing (total rows, filtered rows, percentage).
*   Robust error handling with GUI message boxes.

## Requirements

*   Python 3.x
*   pandas

## Setup

1.  **Clone the repository (or download the files):**
    ```bash
    git clone https://github.com/codenarok/CSVSpecialCharFilter.git
    cd CSVSpecialCharFilter
    ```
2.  **Create and activate a virtual environment (recommended):**
    ```bash
    # On Windows
    python -m venv .venv
    .venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Make sure your virtual environment is activated.
2.  Run the script from the project directory:
    ```bash
    python main.py
    ```
3.  The application window will appear.
    *   Click "Start Processing" to filter a CSV for special characters. You'll be prompted to select an input CSV and then a location to save the filtered output.
    *   Click "Calculate Dimensions" to select a CSV file and view its row and column count.
    *   Click "Exit" to close the application.

## Customization

*   **Columns for Filtering:** Modify the `required_columns` list within the `run_csv_processing` method in `main.py` if you need to check different columns for special characters.
*   **Special Character Definition:** Adjust the regular expression pattern in the `contains_special_characters` static method in `main.py` if your definition of "special characters" differs. The current pattern `r\'[^\\x09\\x0A\\x0D\\x20-\\x7E]\'` targets characters outside the printable ASCII range (excluding tab, newline, carriage return).