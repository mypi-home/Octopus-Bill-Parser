# Octopus Energy Bill Parser

A Python tool to extract and analyze half-hourly energy consumption data from Octopus Energy PDF bills.

## Why This Tool Exists

The Octopus Energy API and website data downloads have limitations:

- **Intelligent Octopus session slots are not available** via the API or website CSV downloads
- **Data is sometimes missing** from the API/website that is correctly recorded in the PDF bills
- The bills contain the **complete and accurate** half-hourly consumption data

This tool extracts that data directly from your PDF bills, giving you:
- `filtered_energy_data.csv` - **Intelligent Octopus bonus slots** (off-peak rates charged outside the standard 23:30-05:30 window), which aren't exposed elsewhere
- `filter_by_date.py` - Exports data in the **same format as Octopus website downloads**, making it easy to fill in gaps or replace missing data

## Features

- 📄 **PDF Extraction** - Automatically extracts energy usage data from Octopus Energy PDF bills
- 📊 **Half-hourly Data** - Parses all 48 daily time periods with rate, consumption (kWh), and cost
- 🕐 **ISO Timestamps** - Generates proper Start/End timestamps with midnight crossing handled correctly
- 📁 **Batch Processing** - Process multiple PDF bills at once
- 🔍 **Filtering Options** - Filter by date range or off-peak periods
- 📈 **CSV Export** - Export data for use in spreadsheets or other analysis tools

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/Octopus-Bill-Parser.git
   cd Octopus-Bill-Parser
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Extract Data from PDF Bills

Place your Octopus Energy PDF bills in the same directory as the script, then run:

```bash
python bill-parser.py
```

This will:
- Process all PDF files in the directory
- Extract half-hourly energy consumption data
- Generate `all_energy_data.csv` with all extracted data
- Generate `filtered_energy_data.csv` with **Intelligent Octopus bonus slots** - periods charged at off-peak rate (6.67p) outside the standard off-peak window (23:30-05:30)

#### Output Columns

| Column | Description |
|--------|-------------|
| Start | Period start timestamp (ISO format) |
| End | Period end timestamp (ISO format) |
| Date | Date of consumption |
| Period | Time period (e.g., "00:00 - 00:30") |
| Rate | Unit rate in pence per kWh |
| Consumption | Energy consumed in kWh |
| Cost | Cost in pence |

### 2. Filter by Date Range

Edit the date range in `filter_by_date.py`:

```python
START_DATE = "15-04-2025"  # DD-MM-YYYY format
END_DATE = "15-05-2025"    # DD-MM-YYYY format
```

Then run:

```bash
python filter_by_date.py
```

This generates `filtered_by_date.csv` in the **same format as Octopus website CSV downloads**, making it easy to fill in missing data or replace incomplete records:

```
Consumption (kwh)    Start                          End
0.802                2025-05-15T00:30:00+01:00     2025-05-15T01:00:00+01:00
```

## Supported Bill Format

This parser is designed for Octopus Energy UK bills that contain:
- Half-hourly consumption data tables
- Date headers in format like "4th December 2024"
- Row format: `HH:MM-HH:MM  rate  consumption  cost`

> **Note:** The regex patterns may need adjustment if your bill format differs slightly.

## Example Output

```
Processing: October_2024_Bill.pdf
Processing: November_2024_Bill.pdf

All data exported to: all_energy_data.csv
Filtered data exported to: filtered_energy_data.csv

Consolidated DataFrame (first few rows):
               Start                 End        Date        Period  Rate  Consumption   Cost
2024-10-01T00:00:00  2024-10-01T00:30:00  2024-10-01  00:00 - 00:30  6.67        0.245  1.634
2024-10-01T00:30:00  2024-10-01T01:00:00  2024-10-01  00:30 - 01:00  6.67        0.198  1.321
```

## Requirements

- Python 3.7+
- pandas
- PyPDF2

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is not affiliated with Octopus Energy. It's an independent project to help users analyze their own energy consumption data.
