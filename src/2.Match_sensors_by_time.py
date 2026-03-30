# -*- coding: utf-8 -*-
"""
Created on Tue Sep  3 13:45:43 2024
Code for match the time between the mobile sensors and the fix sensors at the experiment.

@author: narag

1. Function to find the closest time of the fix sensor network   
2. Apply the function to find matches for each point only if the point matches
3. Creating table with mobile and fix sensors values by point       
4. Statistics Analysis

INPUT: An excel (.xlsx) file with sheets "all_sensors" and "fix_sensors", with the following columns names:
    all sensors: device,	measurement,	Time,	LAeq(1s)
    fix sensor: point,	sensor,	time,	laeq

OUTPUT: A new excel file (.xlsx) with values by sensor
"""
import os
import pandas as pd
import numpy as np
from datetime import timedelta

############################################################################################
#############################               INPUT            ############################### 
############################################################################################

path_ = os.getcwd() 
year = "2024" #CHOOSE BETWEEN "2023" or "2024"
file_path = "/match_sensors_input.xlsx" #ANO 2024

sheet = "all_sensors"
save_file = "yes" #CHOOSE BETWEEN "yes" or no
if save_file == "yes":
    table_name = "match_sensors_output.xlsx" # name of the output file 

############################################################################################
# PREPRARING THE DATASET
############################################################################################

# mobile sensors dataset
if year == "2023": 
    points__ = ['p1', 'p2', 'p3', 'p4']
elif year == "2024":
    points__ = ['caramelo','entrance','grass', 'classroom']
    points__1 = ['caramelo','entrance']
    points__2 = ['grass', 'classroom']
        
mobile_sensors = pd.read_excel(file_path, sheet_name=sheet)  #for ios files
mobile_sensors = mobile_sensors[mobile_sensors['measurement'].isin(points__)]
mobile_sensors.reset_index(drop=True, inplace=True)
mobile_sensors['Time'] = pd.to_datetime(mobile_sensors['Time'], format='%H:%M:%S', errors='coerce').dt.time
mobile_sensors['adjusted_time'] = (pd.to_datetime(mobile_sensors['Time'], format='%H:%M:%S', errors='coerce')).dt.time

# fix sensors dataset
# Convert 'time' to string and clean the 'time' column in 'fix_sensors'
fix_sensors = pd.read_excel(file_path, sheet_name='fix_sensors')
fix_sensors['time'] = fix_sensors['time'].astype(str)  # Ensure all values are strings
fix_sensors['time'] = fix_sensors['time'].str.split(':').str[:2].str.join(':')  # Keep only hours and minutes
fix_sensors['time'] = pd.to_datetime(fix_sensors['time'], format='%H:%M', errors='coerce').dt.time

############################################################################################
############################################################################################
#           1. Function to find the closest time of the fix sensor network     
############################################################################################
############################################################################################

def find_closest_time(row, point, fix_sensors):
    # Filter fix_sensors for the current point
    fix_sensors_point = fix_sensors[fix_sensors['point'] == point]

    # Calculate the time difference
    time_diff = fix_sensors_point['time'].apply(
        lambda t: abs(pd.to_datetime(t.strftime('%H:%M:%S')) - pd.to_datetime(row['adjusted_time'].strftime('%H:%M:%S'))))
    
    # Find the closest time and corresponding Laeq
    closest_index = time_diff.idxmin()
    time_match = fix_sensors_point.loc[closest_index, 'time']
    laeq_match = fix_sensors_point.loc[closest_index, 'laeq']
    sensor_match = fix_sensors_point.loc[closest_index, 'sensor']

    return time_match, laeq_match, sensor_match

# Initialize columns for time_match and laeq_match
mobile_sensors['time_match'] = None
mobile_sensors['laeq_match'] = None
mobile_sensors['sensor_match'] = None

############################################################################################
############################################################################################
#      3. In case there are no reference within smartphones (dataset 2024)
############################################################################################
############################################################################################

def assign_clusters( point, mobile_sensors):
    mobile_sensors['Time'] = pd.to_datetime(mobile_sensors['Time'], format='%H:%M:%S', errors='coerce').dt.time
    mobile_sensors['adjusted_time'] = (pd.to_datetime(mobile_sensors['Time'], format='%H:%M:%S', errors='coerce')).dt.time
    mobile_sensors['Date'] = mobile_sensors['Date'].apply(lambda x: pd.to_datetime(x, dayfirst=True).strftime('%Y-%m-%d'))
    mobile_sensors['datetime'] = pd.to_datetime(mobile_sensors['Date'].astype(str) + ' ' + mobile_sensors['Time'].astype(str), errors='coerce', dayfirst=True)

    # Criar uma lista para os clusters
    clusters = [None] * len(mobile_sensors)
    # Iniciar a operação baseado em um df temporário
    temp_df = mobile_sensors[mobile_sensors['measurement'] == point].sort_values('datetime')
    
    if len(temp_df) <= 1:
        return np.nan
    
    cluster_id = 0
    first_time = None
        
    for idx, temp_row in temp_df.iterrows():
        if first_time is None:
            first_time = temp_row['datetime']
            clusters[temp_row.name] = f"{row['measurement']}_{cluster_id}"
        else:
            # Verifica se a diferença de tempo é maior que 2 minutos
            if (temp_row['datetime'] - first_time).total_seconds() > 40:
                cluster_id += 1
                first_time = temp_row['datetime']  # Atualiza o primeiro tempo
            clusters[temp_row.name] = f"{row['measurement']}_{cluster_id}" 
    return clusters[row.name] 

############################################################################################
############################################################################################
#      3. Apply the function to find matches for each point only if the point matches
############################################################################################
############################################################################################

for index, row in mobile_sensors.iterrows():
    # Extract the point from the sensor name
    device = row['device']
    point = row['measurement']

    if point in points__1:
        time_match, laeq_match, sensor_match  = find_closest_time(row, point, fix_sensors)
        mobile_sensors.loc[index, 'time_match'] = time_match
        mobile_sensors.loc[index, 'laeq_match'] = laeq_match
        mobile_sensors.loc[index, 'sensor_match'] = sensor_match
    elif point in points__2:
        sensor_match = assign_clusters(point, mobile_sensors) 
        mobile_sensors.loc[index, 'sensor_match'] = sensor_match

# Após a iteração, substituir valores únicos em 'sensor_match' para pontos em points__2 por NaN
unique_sensors_points_2 = mobile_sensors[mobile_sensors['measurement'].isin(points__2)]['sensor_match'].value_counts()
unique_sensors = unique_sensors_points_2[unique_sensors_points_2 == 1].index

mobile_sensors.loc[
    (mobile_sensors['measurement'].isin(points__2)) & (mobile_sensors['sensor_match'].isin(unique_sensors)),
    'sensor_match'] = np.nan

############################################################################################
############################################################################################
#             4. Creating table with mobile and fix sensors values by point         
############################################################################################
############################################################################################

laeq_match_wide = mobile_sensors.pivot(index='device', columns='measurement', values='laeq_match')
sensor_match_wide = mobile_sensors.pivot(index='device', columns='measurement', values='sensor_match')
mobileleaq_wide = mobile_sensors.pivot(index='device', columns='measurement', values='LAeq(1s)') 

# Combine the pivoted DataFrames into the desired format
df = mobileleaq_wide.copy()
#df = df.apply(adjust_row, axis=1)
for point in points__:
    df[f'{point}-sensor'] = sensor_match_wide[point]
    #df[f'{point}-laeq'] = laeq_match_wide[point]
    # Convert the columns to numeric
    #df[f'{point}-laeq'] = pd.to_numeric(df[f'{point}-laeq'].astype(str).str.replace(',', '.'), errors='coerce')
df.reset_index(inplace=True)

if save_file == "yes":
    df.to_excel(filepath + "/" + table_name, index=False)
elif save_file == "no":
    print(df)