import pandas as pd
import matplotlib.pyplot as plt
import os

# Load the provided CSV file into a DataFrame
treasury_rates_df = pd.read_csv('data/daily-treasury-rates-2023.csv')

# Extract the most recent data (the first row)
recent_yield_data = treasury_rates_df.iloc[0, 1:].values
maturities = ["5 YR", "7 YR", "10 YR", "20 YR", "30 YR"]

# Ensure the 'charts' directory exists; if not, create it
charts_dir = 'charts'
if not os.path.exists(charts_dir):
    os.makedirs(charts_dir)

# Plotting the yield curve
plt.figure(figsize=(12, 6))
plt.plot(maturities, recent_yield_data, marker='o', color='blue', linestyle='-', linewidth=2)
plt.title(f"Yield Curve on {treasury_rates_df.iloc[0, 0]}", fontsize=16)
plt.xlabel("Maturity", fontsize=14)
plt.ylabel("Yield (%)", fontsize=14)
plt.grid(True, which="both", ls="--", c='0.6')

# Save the plot to the 'charts' directory
chart_path = os.path.join(charts_dir, 'yield_curve_2023.png')
plt.tight_layout()
plt.savefig(chart_path)

# Display the plot
plt.show()
