# Attendance Manager CLI

A small command-line tool to track and manage student attendance per subject using CSV files.

This project stores an overall attendance summary in `Data/Overall/Attendance.csv` and per-subject lecture records in `Data/Subject_Data/` as CSV files. The CLI displays current data and allows adding or toggling attendance entries.

## Features

- Interactive terminal UI for viewing attendance
- Add a new lecture record (present/absent)
- Toggle attendance for an existing lecture date
- Automatic update of totals and attendance percentages

## Requirements

- Python 3.8+
- pandas
- tabulate

You can install the Python dependencies with:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Project layout

```
Data/
	User Config.cfg
	Overall/
		Attendance.csv         # overall summary per subject
	Subject_Data/
		<Subject>.csv          # per-subject lecture rows with Lec_Date and Status
main.py                    # CLI entrypoint
README.md
```

## Usage

Run the CLI from the project root:

```bash
python3 main.py
```

The program will display the current attendance tables and present a simple menu:

1. Add Attendance — choose a subject (by name or index) and mark present (Y) or absent (N). A new lecture row is appended to the subject CSV and overall totals are updated.
2. Toggle Attendance — choose a subject and provide a lecture date (format explained below) to flip that lecture's present/absent status. Totals and percentages are updated accordingly.
3. Exit — quit the program.

### Date format

When toggling attendance the CLI expects a date formatted like:

```
Wed Nov 12 2025
```

This corresponds to Python's `datetime` format string: `%a %b %d %Y`.

## Notes & caveats

- The CLI directly edits CSV files in `Data/`. Keep backups if you need undo history.
- The code uses `pandas` for CSV handling; make sure versions are compatible with your Python release.
- The initial `Data/Overall/Attendance.csv` should contain the expected subject rows for the summary to update correctly.

## Contributing

If you'd like to contribute:

1. Fork the repo and create a branch for your change.
2. Submit a pull request with a clear description of the change.

Small improvements that would help:

- Add unit tests for the attendance logic.
- Add a proper CLI argument parser to support non-interactive usage.

## License

This project currently has no license file. Add one if you intend to open-source it.

---
Generated on: Wed Nov 12 2025
