"""
Created on Wed Sep 11 15:21:10 2024
@author: narag
"""
import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

path_ = os.getcwd() 
from modulo import calculate_LAEQmean_general, devices_time_domain, devices_time_domain_1khz

############################################################################################
#############################               INPUT            ############################### 
############################################################################################
# CHOOSE THE STRING SEPARATOR
year = "2024" #CHOOSE BETWEEN "2023" or "2024"
filter_reference = 'yes' # CHOOSE BETWEEN 'yes' or 'no'
descriptor = "Laeq" #CHOOSE BETWEEN "1Khz" or "Laeq"
dataset = "/dataset" # Folder with the measurements file

# CHOOSE THE REFERENCE AND THE LOCATION
reference = 'LARSON_p1' 
location = 'p1' 

############################################################################################
#############################          PROCESSING            ############################### 
############################################################################################

# Get all unique fix sensors from the matching table
match_sensors  =  pd.read_excel("outputs/match_sensors_output.xlsx", header=0) 
fix_sensors = match_sensors[f'{location}-sensor'].dropna().unique().tolist()
# Dataframe for error results
DELTA = pd.DataFrame(columns=['LA50','LAeq','Δ_LA50','Δ_LAeq'])

for sensor_number in fix_sensors:
    # Find mobile sensors associated with this fix sensor
    mobiles = match_sensors[
        match_sensors[f'{location}-sensor'] == sensor_number]['device'].dropna().unique().tolist() 
    if len(mobiles) == 0:
        continue
    
    # Build file names 
    file_names = [f"{m}_{location}" for m in mobiles]
    file_names.append(f"{sensor_number}_{location}")
    archives = []
    base_path = os.path.join(path_, "dataset")
    for name in file_names:
        pattern = os.path.join(base_path, f"{name}*")
        matches = glob.glob(pattern)
        archives.extend([os.path.abspath(f) for f in matches])

    #def devices_time_domain(arquivos, year, output_name, save_file = None, sensor_number = None)
    if descriptor == "1Khz":
        merged_df = devices_time_domain_1khz(archives, year, "no", "no", sensor_number)
    else:
        merged_df = devices_time_domain(archives, year, "no", "no", sensor_number)

    merged_df.columns = merged_df.columns.str.split("_").str[0]
    # Save the result to Excel
    writer = pd.ExcelWriter(f"outputs/time_series/time_serie_{sensor_number}_{location}.xlsx", engine='xlsxwriter')
    merged_df.to_excel(writer, sheet_name='time_domain', index=False)
    writer.close()
    
    ############################################################################################
    #####################              STATISTIC ANALYSIS           ############################
    ############################################################################################
    
    # Filter the dataframe for timeline of the reference  
    if filter_reference == 'yes':
        merged_df = merged_df[merged_df[sensor_number].notna()]
        merged_df = merged_df.dropna(axis=1, how='all')
        
        # Calculate median and standard deviation for each column
        LA50_ = []
        diff_la50 = {}
        diff_laeq  = []
        
        for col in merged_df.columns:
            if col != 'Time':
                # Filtering the seconds when the reference and device make measurements
                filtered_df = merged_df.dropna(subset=[col, sensor_number])
                count = [col for col in filtered_df.columns if col not in ['Time']]
                if filtered_df.empty:
                    diff_la50[col] = np.nan  
                    diff_laeq.append(np.nan) 
                    continue
                
                # applying the diference
                LA50 = filtered_df[col].median()
                diff_la50[col] = LA50 - filtered_df[sensor_number].median()
                LA50_.append(LA50)  
                
                LAeq = calculate_LAEQmean_general(filtered_df)
                LAeq = pd.Series(LAeq, index=count)
                diff_laeq.append(LAeq[col] - LAeq[sensor_number])
    
        diffs_series = pd.Series(diff_la50)
        diffs_series2 = pd.Series(diff_laeq, index=[col for col in merged_df.columns if col != 'Time'])
        LA50_series = pd.Series(LA50_, index=[col for col in merged_df.columns if col != 'Time'])

        temp_df = pd.DataFrame({
            'LA50': round(LA50_series,2),
            'LAeq': round(LAeq,2),
            'Δ_LA50': round(diffs_series,2),
            'Δ_LAeq': round(diffs_series2,2)})
    
    temp_df = temp_df.reset_index(drop=False)  
    temp_df.rename(columns={'index': 'device'}, inplace=True)  
    
    DELTA = pd.concat([DELTA, temp_df], ignore_index=True)
    
    ############################################################################################
    #####################              GRAPHICAL RESULT            #############################
    ############################################################################################
    # Ensure 'Time' is a string for plotting
    merged_df['Time'] = merged_df['Time'].astype(str)
    
    # Plot
    fig, ax = plt.subplots(figsize=(32,12))
    for column in merged_df.columns:
        if column != 'Time':
            if column == sensor_number: # Plot with black dashed line
                ax.plot(merged_df['Time'], pd.to_numeric(merged_df[column], errors='coerce'), label=column, color='black', linewidth=3,linestyle='--')
            else:
                ax.plot(merged_df['Time'], pd.to_numeric(merged_df[column], errors='coerce'), label=column)

    # Add labels and title
    ax.set_xlabel('Time',fontsize=20)
    ax.set_title('Devices in Time -- location %s -- %s' %(location,sensor_number),fontsize=30)
    if descriptor == "1Khz":
        ax.set_title('Devices in Time -- location %s -- %s --- 1 kHz ----' %(location,sensor_number),fontsize=30)
        ax.set_ylabel('Leq 1kHz (1s)',fontsize=25)
    else:
        ax.set_title('Devices in Time -- location %s -- %s' %(location,sensor_number),fontsize=30)
        ax.set_ylabel('LAeq(1s)',fontsize=25)
    ax.tick_params(axis='both', labelsize=18)  # Ajuste o tamanho da fonte dos valores dos eixos

    # Format x-axis to show time properly
    ax.xaxis.set_major_locator(plt.MaxNLocator(11))  # Limit number of x-ticks
    ax.legend(fontsize=18)  # Add a legend
    ax.grid(True)  # Add a grid
    
    # Save the plot
    plt.savefig(f'outputs/time_series/__delta_{sensor_number}_{location}.png')          
    plt.show()  # Show the plot    

DELTA.to_excel(f'outputs/time_series/__delta_{location}_{descriptor}.xlsx', index=False) 