# -*- coding: utf-8 -*-
"""
Created on Thu Jan 23 17:01:42 2025

@author: narag
"""
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

from modulo import read_frequency_domain

path_ = os.getcwd() 
path_ = path_.split("\\src")[0]

############################################################################################
#############################               INPUT            ############################### 
############################################################################################

filepath = path_ + "/dataset"
openoise_version = "2024"
output_name = "measurements"

# CHOOSE THE REFERENCE (optional)
reference = 'fixsensor-m2' 

############################################################################################
#########################              PROCESSING              #############################
############################################################################################ 

file_names = [arquivo for arquivo in os.listdir(filepath)]

arquivos = [] 
for name in file_names: 
    pattern = os.path.join(filepath, f"{name}*") 
    arquivos.extend(glob.glob(pattern))

##read_files_to_excel(filepath, year, output_name, save_file = None)##
df = read_frequency_domain(filepath, openoise_version, output_name, save_file = "yes")
df.to_excel(path_+'/outputs/frequency_domain_by_filepath/%s.xlsx' %(output_name), index=False)

############################################################################################
#####################              GRAPHICAL RESULT            #############################
############################################################################################
df.columns = df.columns.str.replace('leq_', '')
df.replace(0, pd.NA, inplace=True)

# Definindo as colunas de frequências
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
plt.subplots_adjust(right=0.3)  # Aumenta a margem esquerda para acomodar a legenda
plt.legend(title="Legend", loc='upper left', fontsize=14)
plt.tight_layout()
plt.ylim(20,70)
# Save the plot
plt.savefig(path_ + '/outputs/frequency_domain_by_filepath/frequency_domain_dataset.png', bbox_inches='tight') 
#plt.show()  