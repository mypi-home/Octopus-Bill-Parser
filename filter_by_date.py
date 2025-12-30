import pandas as pd
from datetime import datetime, timedelta
import os

# Configuration - Set your date range here
START_DATE = "17-05-2025"  # DD-MM-YYYY format
END_DATE = "12-07-2025"    # DD-MM-YYYY format

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'all_energy_data.csv')
output_file = os.path.join(script_dir, 'filtered_by_date.csv')

# Read the CSV
df = pd.read_csv(input_file)

# Parse dates for filtering
start_date = datetime.strptime(START_DATE, "%d-%m-%Y").date()
end_date = datetime.strptime(END_DATE, "%d-%m-%Y").date()

# Convert Date column to date type for filtering
df['Date'] = pd.to_datetime(df['Date']).dt.date

# Filter by date range (inclusive)
df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()

# Create Start and End timestamps with timezone offset (+01:00)
def create_start_end_times(row):
    # Parse the period to get start and end times
    period_parts = row['Period'].replace('\n', ' ').split('-')
    start_time = period_parts[0].strip()
    end_time = period_parts[1].strip()
    
    # Create full datetime strings with timezone
    date_str = row['Date'].strftime('%Y-%m-%d')
    start_dt = f"{date_str}T{start_time}:00+01:00"
    
    # Handle end time crossing midnight (e.g., 23:30-00:00 means end is next day)
    start_hour = int(start_time.split(':')[0])
    end_hour = int(end_time.split(':')[0])
    
    if end_hour < start_hour:  # End time is on the next day
        next_day = row['Date'] + timedelta(days=1)
        end_date_str = next_day.strftime('%Y-%m-%d')
    else:
        end_date_str = date_str
    
    end_dt = f"{end_date_str}T{end_time}:00+01:00"
    
    return pd.Series([start_dt, end_dt])

# Apply the function to create Start and End columns
df_filtered[['Start', 'End']] = df_filtered.apply(create_start_end_times, axis=1)

# Create output DataFrame with required columns
df_output = df_filtered[['Consumption', 'Start', 'End']].copy()
df_output.columns = ['Consumption (kwh)', 'Start', 'End']

# Sort by Start time
df_output = df_output.sort_values('Start')

# Export to CSV (tab-separated to match the requested format)
df_output.to_csv(output_file, index=False, sep='\t')

print(f"Filtered data from {START_DATE} to {END_DATE}")
print(f"Total rows: {len(df_output)}")
print(f"Output saved to: {output_file}")
print("\nFirst 10 rows:")
print(df_output.head(10).to_string(index=False))
