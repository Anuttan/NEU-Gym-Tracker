import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime

try:
    df = pd.read_csv(
        'data/facility_data.csv',  # Replace with your filename
        parse_dates=['timestamp_utc', 'updated'],
        dayfirst=False  # Set True if dates use DD/MM format
    )
except FileNotFoundError:
    print("Error: File not found. Please ensure:")
    print("- The CSV file exists in the same directory")
    print("- The filename is spelled correctly")
    exit()

# Data Cleaning
df = df[~df['last_count'].isnull()]
df = df[df['is_closed'] == False]

df['timestamp_utc'] = df['timestamp_utc'] - pd.Timedelta(hours=5) # Move to EST timezone

# Dynamically filter to the last 7 days
max_date = df['timestamp_utc'].max()
one_week_ago = max_date - pd.Timedelta(days=7)
df = df[df['timestamp_utc'] >= one_week_ago]

# Create time-based features
df['date'] = df['timestamp_utc'].dt.date
df['hour'] = df['timestamp_utc'].dt.hour
df['weekday'] = df['timestamp_utc'].dt.day_name()
df['week_number'] = df['timestamp_utc'].dt.isocalendar().week
df['month'] = df['timestamp_utc'].dt.month_name()

# Create visualization grid
plt.figure(figsize=(18, 18))
sns.set_style("darkgrid")
plt.suptitle("Gym Occupancy Analysis (Last 7 Days)", y=1.02, fontsize=16)

# 1. Daily Trend
plt.subplot(2, 2, 1)
daily_avg = df.groupby('date')['last_count'].mean()
daily_avg.plot(kind='line', marker='o', color='royalblue')
plt.title('Daily Average Occupancy')
plt.xlabel('Date')
plt.ylabel('Average People')

# 2. Weekly Pattern
plt.subplot(2, 2, 2)
weekday_order = ['Monday', 'Tuesday', 'Wednesday',
                 'Thursday', 'Friday', 'Saturday', 'Sunday']
weekly_avg = df.groupby('weekday')['last_count'].mean().reindex(weekday_order)
weekly_avg.plot(kind='bar', color='darkorange')
plt.title('Average Occupancy by Weekday')
plt.xlabel('Day of Week')
plt.xticks(rotation=45)

# 3. Hourly Heatmap
plt.subplot(2, 2, 3)
heatmap_data = df.pivot_table(
    values='last_count',
    index='hour',
    columns='weekday',
    aggfunc='mean'
).reindex(columns=weekday_order)
sns.heatmap(heatmap_data, cmap='YlGnBu', annot=True, fmt=".0f")
plt.title('Hourly Occupancy Patterns')
plt.xlabel('Day of Week')
plt.ylabel('Hour of Day')

# 4. Peak Time Distribution
plt.subplot(2, 2, 4)
sns.histplot(data=df, x='hour', bins=24, kde=True, color='purple')
plt.title('Peak Hour Distribution')
plt.xlabel('Hour of Day')
plt.ylabel('Observation Count')

plt.tight_layout()
plt.savefig("assets/gym_occupancy_analysis.png")
