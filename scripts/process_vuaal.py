import pandas as pd
import matplotlib.pyplot as plt
import os

# Load the CSV file into a DataFrame
df = pd.read_csv('data/VUAAL.csv')

# Compute moving averages and add them as new columns
df['ma_10_days'] = df['Adj Close'].rolling(window=10).mean()
df['ma_20_days'] = df['Adj Close'].rolling(window=20).mean()
df['ma_50_days'] = df['Adj Close'].rolling(window=50).mean()

# Ensure the 'charts' directory exists; if not, create it
charts_dir = 'charts'
if not os.path.exists(charts_dir):
    os.makedirs(charts_dir)

# Increase the figure size
plt.figure(figsize=(16, 8))

# Plot 'Adj Close' with increased line width and reduced opacity
plt.plot(df['Date'], df['Adj Close'], label='Adj Close', color='black', linewidth=2, alpha=0.7)

# Plot moving averages with increased line width
plt.plot(df['Date'], df['ma_10_days'], label='10 Day MA', color='red', linestyle='--', linewidth=2.5)
plt.plot(df['Date'], df['ma_20_days'], label='20 Day MA', color='blue', linestyle='--', linewidth=2.5)
plt.plot(df['Date'], df['ma_50_days'], label='50 Day MA', color='green', linestyle='--', linewidth=2.5)

# Adding titles, labels, and other chart details
plt.title('Adjusted Close with Moving Averages', fontsize=16)
plt.xlabel('Date', fontsize=14)
plt.ylabel('Price', fontsize=14)
plt.legend(loc='upper left', fontsize=12)
plt.xticks(df['Date'][::100], rotation=45, fontsize=10)
plt.grid(True, which="both", ls="--", c='0.6')

# Save the enhanced plot to the 'charts' directory
chart_path = os.path.join(charts_dir, 'adjusted_close_with_moving_averages.png')
plt.tight_layout()
plt.savefig(chart_path)

# Display the enhanced plot
plt.show()
