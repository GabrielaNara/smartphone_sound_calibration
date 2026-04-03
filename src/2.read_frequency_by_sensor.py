# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 17:01:42 2025

@author: narag
"""
import os
import glob
import pandas as pd
import shutil
import matplotlib.pyplot as plt

path_ = os.getcwd() 
from modulo import read_frequency_domain
path_ = path_.split("\\src")[0]

############################################################################################
#############################               INPUT            ############################### 
############################################################################################

# CHOOSE INPUT
location = 'looping' #in the example: p1 or p2. OR choose "looping" for iterate between all locations

# DEFAULT PARAMETERS
y_min = 20
y_max = 70
openoise_version = "2024" #CHOOSE BETWEEN "2023" or "2024"
descriptor = "LAeq" #CHOOSE BETWEEN "1Khz" or "Laeq"
output_name = "measurements"
fix_path = os.path.join(path_, "dataset/fix_sensors") #filepath where to find the fix_sensors
mobile_path =  os.path.join(path_, "dataset/mobile_sensors")  #filepath where to find the mobile_sensors
calibration_table =  pd.read_excel(path_ + "/dataset/input.xlsx",sheet_name="fix_sensors")

############################################################################################
#########################              PROCESSING              #############################
############################################################################################ 

# choose if it process or not the looping
if location == "looping":
    locations = calibration_table['location'].dropna().unique()
else: 
    locations = [location]
    
for location in locations:  
    # Get all unique fix sensors from the matching table
    match_sensors  =  pd.read_excel(path_+"/outputs/match_sensors_output.xlsx", header=0) 
    fix_sensors = match_sensors[f'{location}-sensor'].dropna().unique().tolist()
    
    # Create a temporary filepath do add the files
    temp_dir = path_ + "/dataset/temp"
    
    for sensor_number in fix_sensors:
        # clear the existent content in the tempoerary file
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        
        #for sensor_number in fix_sensors: #if you want to iteract with many sensors
        reference = sensor_number  # IN CASE YOU PREFER A UNIQUE SENSOR
        mobiles = match_sensors[
            match_sensors[f'{location}-sensor'] == sensor_number]['device'].dropna().unique().tolist() 
        
        # --- copy mobile-sensors to a temporary path ---
        for m in mobiles:
            pattern = os.path.join(mobile_path, f"{m}_{location}*")
            for file in glob.glob(pattern):
                shutil.copy(file, os.path.join(temp_dir, os.path.basename(file)))      
        # --- copy fix-sensors to a temporary path ---
        pattern_fix = os.path.join(fix_path, f"{sensor_number}_{location}*")
        for file in glob.glob(pattern_fix):
            shutil.copy(file, os.path.join(temp_dir, os.path.basename(file)))
            
        # --- APPLY FREQUENCY DOMAIN FUNCTION ---
        df = read_frequency_domain(temp_dir, openoise_version,  output_name, save_file = "yes")
        
        # ADDING Location geoposition (if not given) 
        calibration_table ["temp"] = calibration_table["device"] + "_" + calibration_table["location"]
        #calibration_table = calibration_table.set_index(['device', 'location'])
        for col in ['x', 'y']:
            df[col] = [
                calibration_table[col].get((dev.split('-')[0], loc), old)
                for dev, loc, old in zip(df['device'], df['measurement'], df[col])]
        
        #specific issue with a device
        freq_colunas = ['LAeq(1s)','leq_100', 'leq_125', 'leq_160', 'leq_200', 'leq_250', 'leq_315',
        'leq_400', 'leq_500', 'leq_630', 'leq_800', 'leq_1000', 'leq_1250',
        'leq_1600', 'leq_2000', 'leq_2500', 'leq_3150', 'leq_4000', 'leq_5000',
        'leq_6300', 'leq_8000', 'leq_10000', 'leq_12500', 'leq_16000']   
        mask = df["device"].str.startswith("samsungA7", na=False)
        df.loc[mask, freq_colunas] = df.loc[mask, freq_colunas].add(0.5) 
    
        # Save the file
        os.makedirs(path_+'/outputs/frequency_domain_by_sensor', exist_ok=True)
        df.to_excel(path_+f'/outputs/frequency_domain_by_sensor/frequency_{sensor_number}_{location}.xlsx', index=False)
        
        ############################################################################################
        #####################              GRAPHICAL RESULT            #############################
        ############################################################################################
        df.columns = df.columns.str.replace('leq_', '')
        df.replace(0, pd.NA, inplace=True)
        
        # Defining the columns for the figure
        freq_columns = ['63','80','100', '125', '160', '200', '250', '315', '400', '500',
               '630', '800', '1000', '1250', '1600', '2000', '2500', '3150', '4000',
               '5000', '6300', '8000', '10000', '12500', '16000']
        
        # Plot
        plt.figure(figsize=(14, 7), dpi=300)
        for i, row in df.iterrows():
            row_clean = pd.to_numeric(row[freq_columns], errors='coerce')
            device = row['device']
            if device.startswith(reference):
                plt.plot(freq_columns, row_clean, label=device, color="black", linestyle='--', linewidth=4)  
            else:
                plt.plot(freq_columns, row_clean, label=device, linewidth=2)
        plt.ylabel("Sound Pressure Level (dBA)", fontsize=18, labelpad=10)
        plt.xlabel("Frequency (Hz)", fontsize=18, labelpad=10)
        plt.xticks(rotation=45, fontsize=16) 
        plt.yticks(fontsize=16)
        plt.grid(True, color='#E0E0E0')
        plt.subplots_adjust(right=0.3)  
        plt.legend(title="Legend", loc='upper left', fontsize=14)
        plt.tight_layout()
        plt.ylim(y_min,y_max)
        plt.savefig(path_+ f'/outputs/frequency_domain_by_sensor/frequency_{sensor_number}_{location}.png', bbox_inches='tight') # Save the file
        plt.show()  