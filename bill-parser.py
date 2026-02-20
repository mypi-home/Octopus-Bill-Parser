# How It Works
# PDF Extraction:
# The script reads your PDF file starting from page index 3 (which corresponds to physical page 4 onward) and concatenates the text.

# Parsing Dates and Rows:

# It uses a regex to find date markers (e.g. “4th December 2024”).
# Then, for each date block, it extracts rows using a regex pattern that expects a half-hour period, a rate, consumption, and cost.
# Data Consolidation:
# All rows are stored in a list and then converted into a pandas DataFrame.

# Filtering:
# A helper function checks if the starting time of the period is within the off-peak window (before 05:30 or from 23:30 onward). The DataFrame is filtered to retain only those rows where the rate is 6.67p and the period is not off-peak.

# You can adjust the regex patterns if the formatting in your PDF differs slightly. This should consolidate your data and produce the desired filtered view.

import re
from datetime import datetime
try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo
import pandas as pd
import PyPDF2
import os
import glob

# Define the timezone for all dates and times ("Europe/London")
meter_timezone_string = "Europe/London"

# Define a helper function to remove ordinal suffixes from day numbers in dates
def remove_ordinal_suffix(s):
    return re.sub(r'(\d{1,2})(st|nd|rd|th)', r'\1', s)

# Define a regex pattern to capture dates in the format like "4th December 2024"
date_pattern = r"(\d{1,2}(?:st|nd|rd|th)\s+\w+\s+\d{4})"

# Define a regex to capture each half-hour row.
# This pattern assumes rows are formatted like:
# "00:00-00:30   6.67   7.36   49.042"
row_pattern = re.compile(r"(\d{2}:\d{2}\s*-\s*\d{2}:\d{2})\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)")

def process_pdf(pdf_path):
    """Process a single PDF file and return its data rows"""
    data_rows = []
    pdf_reader = PyPDF2.PdfReader(open(pdf_path, "rb"))
    all_text = ""
    for i in range(1, len(pdf_reader.pages)):
        page = pdf_reader.pages[i]
        page_text = page.extract_text()
        if page_text:
            all_text += page_text + "\n"

    # Find all date markers
    date_matches = list(re.finditer(date_pattern, all_text))
    
    # Process each date block
    for idx, date_match in enumerate(date_matches):
        date_str = date_match.group(1)
        date_clean = remove_ordinal_suffix(date_str)
        try:
            date_parsed = datetime.strptime(date_clean, "%d %B %Y").date()
        except Exception as e:
            print(f"Error parsing date '{date_clean}' in {pdf_path}:", e)
            continue

        start_index = date_match.end()
        end_index = date_matches[idx + 1].start() if idx + 1 < len(date_matches) else len(all_text)
        block = all_text[start_index:end_index]
        
        for row in row_pattern.findall(block):
            period, rate, consumption, cost = row
            data_rows.append({
                "Date": date_parsed,
                "Period": period.strip().replace('\n', ' '),
                "Rate": float(rate),
                "Consumption": float(consumption),
                "Cost": float(cost)
            })
    
    return data_rows

# Get all PDF files in the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
pdf_files = glob.glob(os.path.join(script_dir, "*.pdf"))

if not pdf_files:
    print("No PDF files found in directory:", script_dir)
    exit(1)

# Process all PDFs and collect their data
all_data_rows = []
for pdf_path in pdf_files:
    print(f"Processing: {pdf_path}")
    all_data_rows.extend(process_pdf(pdf_path))

# Define a helper function to create ISO timestamps (Start and End) from date and period
def create_timestamps(row):
    from datetime import timedelta
    # Extract start and end times from period
    period_parts = row['Period'].replace('\n', ' ').split('-')
    start_time_str = period_parts[0].strip()
    end_time_str = period_parts[1].strip()
    
    # Create start datetime
    start_dt = datetime.combine(row['Date'], datetime.strptime(start_time_str, '%H:%M').time(), tzinfo=zoneinfo.ZoneInfo(meter_timezone_string)).replace(fold=row['FoldStart'])
    
    # Create end datetime - handle midnight crossing
    start_hour = int(start_time_str.split(':')[0])
    end_hour = int(end_time_str.split(':')[0])
    
    if end_hour < start_hour:  # End time is on the next day (e.g., 23:30-00:00)
        end_date = row['Date'] + timedelta(days=1)
    else:
        end_date = row['Date']
    
    end_dt = datetime.combine(end_date, datetime.strptime(end_time_str, '%H:%M').time(), tzinfo=zoneinfo.ZoneInfo(meter_timezone_string)).replace(fold=row['FoldEnd'])
    
    return pd.Series([start_dt.isoformat(), end_dt.isoformat(), start_dt])

# After creating the DataFrame, set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

# Create a DataFrame with all the consolidated data
df = pd.DataFrame(all_data_rows)

#If the DataFrame is empty then there is nothing to process - and later fuctions will fail. So check
if df.empty:
    #If empty print a message and populate dataframe with nothing - so export will work
    print("No half-hourly rows found.")
    df[['Start', 'End', 'Date', 'Period', 'Rate', 'Consumption', 'Cost']] = None
else:
    # Check which value of fold we need to use - by looking for cases where the current row time (start or end) is the same value as two rows back
    # Add a column for each
    # True means this 'wall time' is the second time we have seen this value, so the time stamp needs to be set to the later occurrence
    df['FoldStart'] = df.Period.str[0:5] == df.Period.shift(2,fill_value="").str[:5]
    df['FoldEnd'] = df.Period.str[8:13] == df.Period.shift(2,fill_value="").str[-5:]

    # Add Start and End timestamp columns
    df[['Start', 'End', 'StartTimestamp']] = df.apply(create_timestamps, axis=1)

    # Convert the rate column to a number
    df['Rate'] = df['Rate'].astype(float)

    # Sort by Start timestamp to ensure chronological order
    df = df.sort_values('StartTimestamp')

# Reduce columns to only those that are needed for export
df = df[['Start', 'End', 'Date', 'Period', 'Rate', 'Consumption', 'Cost']]

# Define a helper function to determine if the period starts during the off-peak window (23:30 - 05:30)
def is_offpeak(period_str):
    start_str = period_str.replace('\n', ' ').split('-')[0].strip()
    start_time = datetime.strptime(start_str, "%H:%M").time()
    offpeak_start = datetime.strptime("23:30", "%H:%M").time()
    offpeak_end = datetime.strptime("05:30", "%H:%M").time()
    # Because the off-peak window spans midnight,
    # we consider times from 23:30 to midnight OR from midnight to 05:30 as off-peak.
    return (start_time >= offpeak_start) or (start_time < offpeak_end)

# Filter the DataFrame:
# Select rows where Rate is 'off-peak' and the period is NOT off-peak.
# To allow for changing rates over time, including during one bill, 'off peak' will be any rate under 8p
df_filtered = df[(df['Rate'] < 8.0) & (~df['Period'].apply(is_offpeak))]

# Export both DataFrames to CSV with absolute paths and debug output
# Create full paths for CSV files
all_data_path = os.path.join(script_dir, 'all_energy_data.csv')
filtered_data_path = os.path.join(script_dir, 'filtered_energy_data.csv')

# Export with error handling
try:
    df.to_csv(all_data_path, index=False)
    print(f"\nAll data exported to: {all_data_path}")
except Exception as e:
    print(f"Error saving all_energy_data.csv: {e}")

try:
    df_filtered.to_csv(filtered_data_path, index=False)
    print(f"Filtered data exported to: {filtered_data_path}")
except Exception as e:
    print(f"Error saving filtered_energy_data.csv: {e}")

# Show results with improved formatting
print("\nConsolidated DataFrame (first few rows):")
print(df.head().to_string(index=False))
print("\nFiltered DataFrame (Rate < 8.00p outside off-peak 23:30-05:30):")
print(df_filtered.to_string(index=False))
