import os
import glob
import re
import pandas as pd

def determine_season(month):
    """
    Determines the season based on the month number.
    In Australia:
      - Summer: December, January, February
      - Autumn: March, April, May
      - Winter: June, July, August
      - Spring: September, October, November
    """
    if month in [12, 1, 2]:
        return "Summer"
    elif month in [3, 4, 5]:
        return "Autumn"
    elif month in [6, 7, 8]:
        return "Winter"
    elif month in [9, 10, 11]:
        return "Spring"
    else:
        return "Unknown"

def main():
    # Define the folder containing the temperature CSV files (wide-format files)
    folder_path = r"C:\Users\ingram\Desktop\assignment\temperature_data"
    
    # List all CSV files in the folder (match both .csv and .CSV)
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
    csv_files += glob.glob(os.path.join(folder_path, "*.CSV"))
    
    if not csv_files:
        print("No CSV files found in the specified folder.")
        return

    # List to hold long-format DataFrames from each CSV file
    df_list = []
    
    # Define the list of month names (expected column names)
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
    # Map month names to month numbers
    month_to_number = {name: i for i, name in enumerate(month_names, start=1)}
    
    for file in csv_files:
        df = pd.read_csv(file, encoding="utf-8")
        print(f"Processing file: {file}")
        print("Columns found:", df.columns.tolist())
        
        # In these files, the temperature values are in the month columns.
        available_months = [col for col in df.columns if col in month_names]
        if not available_months:
            raise KeyError(f"Month columns not found in file: {file}")
        
        # Determine station column. 
        if "STATION_NAME" in df.columns:
            station_col = "STATION_NAME"
        elif "station" in df.columns:
            station_col = "station"
        else:
            raise KeyError(f"Station column not found in file: {file}")
        
        # Optionally, extract year from filename using regular expression.
        m = re.search(r'(\d{4})', os.path.basename(file))
        if m:
            year_val = int(m.group(1))
        else:
            year_val = None
        
        # Convert wide format to long format using melt.
        # id_vars: the station information. Here只保留站名
        df_long = pd.melt(df,
                          id_vars=[station_col],
                          value_vars=available_months,
                          var_name="MonthName",
                          value_name="Temperature")
        
        # Add a column for Year if available
        if year_val is not None:
            df_long["Year"] = year_val
        
        # Convert Temperature to numeric, errors coerced to NaN then drop these rows
        df_long["Temperature"] = pd.to_numeric(df_long["Temperature"], errors="coerce")
        df_long = df_long.dropna(subset=["Temperature"])
        
        # Map MonthName to month number
        df_long["Month"] = df_long["MonthName"].map(month_to_number)
        
        # Determine the season from the month number
        df_long["Season"] = df_long["Month"].apply(determine_season)
        
        # Rename station column to standard name "Station"
        df_long = df_long.rename(columns={station_col: "Station"})
        
        df_list.append(df_long)
    
    # Concatenate all long-format DataFrames into a master DataFrame
    master_df = pd.concat(df_list, ignore_index=True)
    
    # -------------------- TASK 1 --------------------
    # Calculate the average temperatures for each season across all years.
    season_avg = master_df.groupby("Season")["Temperature"].mean()
    
    average_temp_file = r"C:\Users\ingram\Desktop\assignment\average_temp.txt"
    with open(average_temp_file, "w", encoding="utf-8") as f:
        f.write("Average Temperature by Season:\n")
        for season, avg_temp in season_avg.items():
            f.write(f"{season}: {avg_temp:.2f}\n")
    
    # -------------------- TASK 2 --------------------
    # Calculate the temperature range (max - min) for each station.
    station_range = master_df.groupby("Station")["Temperature"].agg(lambda x: x.max() - x.min())
    max_range = station_range.max()
    # Find the station(s) with the largest temperature range.
    stations_largest_range = station_range[station_range == max_range].index.tolist()
    
    largest_range_file = r"C:\Users\ingram\Desktop\assignment\largest_temp_range_station.txt"
    with open(largest_range_file, "w", encoding="utf-8") as f:
        f.write("Station(s) with the Largest Temperature Range:\n")
        f.write(f"Temperature Range: {max_range:.2f}\n")
        for station in stations_largest_range:
            f.write(f"{station}\n")
    
    # -------------------- TASK 3 --------------------
    # Calculate the average temperature for each station.
    station_avg = master_df.groupby("Station")["Temperature"].mean()
    
    # Find the warmest station(s) based on the highest average temperature.
    max_avg = station_avg.max()
    warmest_stations = station_avg[station_avg == max_avg].index.tolist()
    
    # Find the coolest station(s) based on the lowest average temperature.
    min_avg = station_avg.min()
    coolest_stations = station_avg[station_avg == min_avg].index.tolist()
    
    warmest_coolest_file = r"C:\Users\ingram\Desktop\assignment\warmest_and_coolest_station.txt"
    with open(warmest_coolest_file, "w", encoding="utf-8") as f:
        f.write("Warmest and Coolest Stations:\n")
        f.write("Warmest Station(s):\n")
        f.write(f"Average Temperature: {max_avg:.2f}\n")
        for station in warmest_stations:
            f.write(f"{station}\n")
        f.write("\nCoolest Station(s):\n")
        f.write(f"Average Temperature: {min_avg:.2f}\n")
        for station in coolest_stations:
            f.write(f"{station}\n")
    
    print("Data analysis complete. Results saved to output files.")

if __name__ == "__main__":
    main()
