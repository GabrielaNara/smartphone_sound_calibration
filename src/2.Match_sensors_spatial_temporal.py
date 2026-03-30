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
import glob
import pandas as pd
import geopandas as gpd

from modulo import read_frequency_domain

path_ = os.getcwd() 
path_ = path_.split("\\src")[0]

############################################################################################
#############################               INPUT            ############################### 
############################################################################################

openoise_version = "2024" #CHOOSE BETWEEN "2023" or "2024"
file_path = "calibration-devices.xlsx" #ANO 2024
save_file = "yes" #CHOOSE BETWEEN "yes" or no

time_tolerance = "3min"
participants_informed_location = "yes" #CHOOSE BETWEEN "yes" or "no" related if location is already provided

############################################################################################
# PREPRARING THE DATASET
############################################################################################

# --- FIX SENSORS ---
filepath_temp = path_+"/dataset/fix_sensors"
archives = []
for root, dirs, files in os.walk(filepath_temp):
    for file in files:
        temp_path = os.path.join(root, file)
        archives.append(temp_path)

# adjust time        
fix_sensors = read_frequency_domain(filepath_temp, openoise_version)
fix_sensors['datetime'] = pd.to_datetime(
    fix_sensors['Date'].astype(str) + ' ' + fix_sensors['Time'].astype(str), dayfirst=True,   errors='coerce') 

# --- MOBILE SENSORS ---
filepath_temp =  path_+"/dataset/mobile_sensors"
file_names = [arquivo for arquivo in os.listdir(filepath_temp)]
arquivos = [] 
for name in file_names: 
    pattern = os.path.join(filepath_temp) 
    arquivos.extend(glob.glob(pattern))
# adjust time      
mobile_sensors = read_frequency_domain(filepath_temp, openoise_version)
mobile_sensors['datetime'] = pd.to_datetime(
    mobile_sensors['Date'].astype(str) + ' ' + mobile_sensors['Time'].astype(str),dayfirst=True,errors='coerce')

# ADDING Location geoposition (if not given) 
calibration_table =  pd.read_excel(path_ + "/calibration-devices.xlsx",sheet_name="fix_sensors")
fix_sensors = fix_sensors.drop(columns=['x', 'y', 'z'], errors='ignore')
fix_sensors = fix_sensors.merge(
    calibration_table[['location', 'x', 'y', 'z']],left_on='measurement',
    right_on='location',how='left').drop(columns='location')

############################################################################################
############################################################################################
#           1. SPATIAL MATCHING  
############################################################################################
############################################################################################

# --- FIX SENSORS ---
fix_unique = fix_sensors.drop_duplicates(subset=['x','y'])
gdf_fix = gpd.GeoDataFrame(fix_unique,geometry=gpd.points_from_xy(fix_unique['y'], fix_unique['x']),crs="EPSG:4326")
gdf_fix = gdf_fix.to_crs(epsg=3857)

# --- MOBILE SENSORS ---
gdf_mobile = gpd.GeoDataFrame(mobile_sensors,geometry=gpd.points_from_xy(mobile_sensors['x'], mobile_sensors['y']),crs="EPSG:4326")
gdf_mobile = gdf_mobile.to_crs(epsg=3857)

# --- SJOIN_NEAREST  --- 
joined = gpd.sjoin_nearest(
    gdf_mobile,
    gdf_fix[['measurement', 'geometry']],
    how='left',
    distance_col='distance')

mobile_sensors['nearest_location'] = joined['measurement_right'].values
mobile_sensors['nearest_distance'] = joined['distance'].values

############################################################################################
############################################################################################
#           2. TEMPOERAL MATCHING  
############################################################################################
############################################################################################

# loop por location
for location in mobile_sensors['measurement'].dropna().unique():

    # --- FIX SENSORS ---
    fix_filtered = fix_sensors[fix_sensors['measurement'] == location].copy()
    fix_filtered = fix_filtered.dropna(subset=['datetime'])
    fix_filtered = fix_filtered.rename(columns={'datetime': 'datetime_fix'}).sort_values('datetime_fix')

    # --- MOBILE SENSORS ---
    if participants_informed_location == "no":
        mobile_mask = mobile_sensors['nearest_location'] == location
    if participants_informed_location == "yes":
        mobile_mask = mobile_sensors['measurement'] == location        
    mobile_filtered = mobile_sensors.loc[mobile_mask].copy()
    mobile_filtered = mobile_filtered.dropna(subset=['datetime']).sort_values('datetime')

    # --- MERGE ASOF ---
    merged = pd.merge_asof(
        mobile_filtered,
        fix_filtered[['measurement', 'datetime_fix', 'device']],
        left_on='datetime',
        right_on='datetime_fix',
        by='measurement',
        direction='nearest',
        tolerance=pd.Timedelta(time_tolerance))

    # --- ESCREVER DE VOLTA NO DATAFRAME ORIGINAL ---
    mobile_sensors.loc[mobile_filtered.index, 'match_fix_sensor'] = merged['device_y'].values
    mobile_sensors.loc[mobile_filtered.index, 'time_fix_sensor'] = merged['datetime_fix'].values

############################################################################################
############################################################################################
#             3. Creating table with mobile and fix sensors values by point         
############################################################################################
############################################################################################

# --- PIVOTS ---
sensor_match_wide = mobile_sensors.pivot(index='device',columns='measurement',
    values='match_fix_sensor')   # columns name

mobileleaq_wide = mobile_sensors.pivot(index='device',columns='measurement',
    values='Time')   # columns name

# Combine the pivoted DataFrames into the desired format
df = mobileleaq_wide.copy()
for point in sensor_match_wide.columns:  
    df[f'{point}-sensor'] = sensor_match_wide[point]
df = df.reset_index()

if save_file == "yes":
    df.to_excel(path_ + "/outputs/match_sensors_output.xlsx" , index=False)
elif save_file == "no":
    print(df)