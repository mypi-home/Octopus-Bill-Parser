import argparse
import pandas as pd
from datetime import datetime
import os

# Configuration - Set your date range here
START_DATE = "29-12-2025"  # DD-MM-YYYY format
END_DATE = "12-07-2026"    # DD-MM-YYYY format


def parse_args():
	parser = argparse.ArgumentParser(
		description="Filter all_energy_data.csv by date range and export Octopus-style output."
	)
	parser.add_argument(
		"--start-date",
		default=START_DATE,
		help="Start date in DD-MM-YYYY format. Defaults to START_DATE in the script.",
	)
	parser.add_argument(
		"--end-date",
		default=END_DATE,
		help="End date in DD-MM-YYYY format. Defaults to END_DATE in the script.",
	)
	return parser.parse_args()


args = parse_args()

# Get the script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
input_file = os.path.join(script_dir, 'all_energy_data.csv')
output_file = os.path.join(script_dir, 'filtered_by_date.csv')

# Read the CSV
df = pd.read_csv(input_file)

# Parse dates for filtering
start_date = datetime.strptime(args.start_date, "%d-%m-%Y").date()
end_date = datetime.strptime(args.end_date, "%d-%m-%Y").date()

# Convert Date column to date type for filtering
df['Date'] = pd.to_datetime(df['Date']).dt.date

# Filter by date range (inclusive)
df_filtered = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)].copy()

# Create output DataFrame with required columns
df_output = df_filtered[['Consumption', 'Start', 'End']].copy()
df_output.columns = ['Consumption (kwh)', 'Start', 'End']

# Sort by Start time
df_output = df_output.sort_values('Start')

# Export to CSV (tab-separated to match the requested format)
df_output.to_csv(output_file, index=False, sep='\t')

print(f"Filtered data from {args.start_date} to {args.end_date}")
print(f"Total rows: {len(df_output)}")
print(f"Output saved to: {output_file}")
print("\nFirst 10 rows:")
print(df_output.head(10).to_string(index=False))
