import pandas as pd
import os
path_ = os.getcwd() 

############################################################################################
#############################              INPUT            ################################
############################################################################################

year = "2023"
comparson_value = "LA50"  #CHOOSE the value to compare: LA50 or LAeq
filepath = path_ + f"/1.CALIBRATION/{year}"

# YEAR 2023 --> p1 = caramelo; p2 = avenue,     p3 = phisics, p4 = forest
# YEAR 2024 --> p1 = caramelo; p2 = entrance,   p3 = grass,   p4 = classroom
df1 = pd.read_excel(filepath + "/_graphs_by_fixsensor/__delta_p1.xlsx")
df2 = pd.read_excel(filepath + "/_graphs_by_fixsensor/__delta_p2.xlsx")
df3 = pd.read_excel(filepath + "/_graphs_by_fixsensor/__delta_p3.xlsx")
df4 = pd.read_excel(filepath + "/_graphs_by_fixsensor/__delta_p4.xlsx")

if year == "2023":
    df3 = pd.read_excel(filepath + "/graphs_by_fixsensor/__delta_p3_class2.xlsx")
    df4 = pd.read_excel(filepath + "/graphs_by_fixsensor/__delta_p4_class2.xlsx")

# PRE-CALIBRATION VALUES AND DEVICE MODEL  
df_TABLE =  pd.read_excel(filepath + "/calibration-devices.xlsx",sheet_name="geral")
df_TABLE = df_TABLE[['device', 'device_model', 'gain_calibration']]

############################################################################################
######################                  PROCESSING              ############################
############################################################################################

df1['device'] = df1['device'].apply(lambda x: x.split('_')[0])
df2['device'] = df2['device'].apply(lambda x: x.split('_')[0])
df3['device'] = df3['device'].apply(lambda x: x.split('_')[0])
df4['device'] = df4['device'].apply(lambda x: x.split('_')[0])

df_TABLE['slm1_p1'] = None
df_TABLE['slm1_p2'] = None #In the year 2024 it was a smartphone, but keep like this
df_TABLE['blind_p1'] = None
df_TABLE['blind_p2'] = None
df_TABLE['blind_p3'] = None
df_TABLE['blind_p4'] = None
if year == "2023":
    df_TABLE['slm2_p3'] = None
    df_TABLE['slm2_p4'] = None 

def buscar_valor(df, device, column):
    # Tenta encontrar o valor correspondente no dataframe
    resultado = df[df['device'] == device]
    
    # Se encontrar, retorna o valor de ERROR
    if not resultado.empty:
        return resultado[column].values[0]*(-1)
    else:
        return None  # Retorna None se o device não for encontrado

# Iterar sobre cada linha do df_TABLE
for index, row in df_TABLE.iterrows():
    device = row['device']
    
    # Buscar os valores de ERROR em cada dataframe
    df_TABLE.at[index, 'slm1_p1'] = buscar_valor(df1, device,'Δ_%s' %comparson_value)
    df_TABLE.at[index, 'slm1_p2'] = buscar_valor(df2, device,'Δ_%s' %comparson_value)
    df_TABLE.at[index, 'blind_p1'] = buscar_valor(df1, device,'blind_%s' %comparson_value)
    df_TABLE.at[index, 'blind_p2'] = buscar_valor(df2, device,'blind_%s' %comparson_value)   
    df_TABLE.at[index, 'blind_p3'] = buscar_valor(df3, device,'blind_%s' %comparson_value)
    df_TABLE.at[index, 'blind_p4'] = buscar_valor(df4, device,'blind_%s' %comparson_value)   
    if year == "2023":
        df_TABLE.at[index, 'slm2_p3'] = buscar_valor(df3, device,'Δ_%s' %comparson_value)
        df_TABLE.at[index, 'slm2_p4'] = buscar_valor(df4, device,'Δ_%s' %comparson_value)

# Convert columns to numeric
for col in df_TABLE.columns:
    if col not in ["device", "device_model"]:
        df_TABLE[col] = pd.to_numeric(df_TABLE[col], errors='coerce')
    else:
        df_TABLE[col] = df_TABLE[col].astype(str)
        
# check the results
df_iphone = df_TABLE[df_TABLE['device_model'].str.contains('Iphone', case=False, na=False)]
df_samsung = df_TABLE[df_TABLE['device_model'].str.contains('SM', case=False, na=False)]
df_others = df_TABLE[~df_TABLE['device_model'].str.contains('Iphone', case=False, na=False) & 
                             ~df_TABLE['device_model'].str.contains('SM', case=False, na=False)]
len(df_iphone)
len(df_samsung)
len(df_others)

writer = pd.ExcelWriter(filepath + '/_analysis.xlsx', engine='xlsxwriter')
df_TABLE.to_excel(writer, index=False)
writer.close()

print("CONCLUÍDO! O arquivo '_analysis.xlsx' foi criado com sucesso.")

############################################################################################
#####################              TRUE CALIBRATION             ############################
############################################################################################
import numpy as np
import matplotlib.pyplot as plt

#analysis = df_TABLE.copy()
analysis =  pd.read_excel(filepath + "/calibration-devices.xlsx",sheet_name="geral")

import scipy.stats as stats

def true_calibration(df):
    df['true_calibration2'] = None
    
    # Se slm1_p1 e slm1_p2 forem NaN e slm2_p3 não for NaN -> usa slm2_p3 - LAB
    maskLAB = df['gain_calibration'].notna()
    df.loc[maskLAB, 'true_calibration2'] = df.loc[maskLAB, 'gain_calibration']*-1
    
    # Se a coluna 'LAB' for NaN, substitui por 0
    df['gain_calibration'] = df['gain_calibration'].fillna(0)
    
    # Máscaras básicas
    mask1 = df['slm1_p1'].notna()
    mask2 = df['slm1_p1'].isna() & df['slm1_p2'].notna()
    mask3 = df['slm1_p1'].isna() & df['slm1_p2'].isna() & df['slm2_p4'].notna()

    # Aplica as condições principais
    df.loc[mask1, 'true_calibration2'] = df.loc[mask1, 'slm1_p1'] - df.loc[mask1, 'gain_calibration']
    df.loc[mask2, 'true_calibration2'] = df.loc[mask2, 'slm1_p2'] - df.loc[mask2, 'gain_calibration']
    df.loc[mask3, 'true_calibration2'] = df.loc[mask3, 'slm2_p4'] - df.loc[mask3, 'gain_calibration']

    # Agora, se o fabricante for IOS, adiciona +24
    ios_mask = df['group_manufacturer'] == 'IOS'
    df.loc[ios_mask, 'true_calibration2'] = df.loc[ios_mask, 'true_calibration2'] + 24

    return df

analysis = true_calibration(analysis)  

def stdev_calibration(df):
    slm1_p1_valid = df['slm1_p1'].notna() & (df['slm1_p1'] != 0)
    slm1_p2_valid = df['slm1_p2'].notna() & (df['slm1_p2'] != 0)
    slm2_p4_valid = df['slm2_p4'].notna() & (df['slm2_p4'] != 0)

    condicoes = [
        slm1_p1_valid & slm1_p2_valid & ~slm2_p4_valid,
        slm1_p1_valid & slm1_p2_valid & slm2_p4_valid,
        ~slm1_p1_valid & slm1_p2_valid & ~slm2_p4_valid,
        ~slm1_p1_valid & slm1_p2_valid & slm2_p4_valid
    ]

    valores = [
        df['slm1_p1'] - df['slm1_p2'],
        ((df['slm1_p1'] - df['slm1_p2']) + (df['slm1_p1'] - df['slm2_p4'])) / 2,
        np.nan,
        df['slm1_p2'] - df['slm2_p4']
    ]

    df['stdev_calibration'] = np.select(condicoes, valores, default=np.nan)
    
    df['stdev_calibration'] = df['stdev_calibration'].abs()
    return df

analysis = stdev_calibration(analysis)  

# SAVE FILE
analysis.to_excel(filepath + '/calibration_devices_code.xlsx', index=False)   