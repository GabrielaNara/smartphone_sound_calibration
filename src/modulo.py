# -*- coding: utf-8 -*-
"""
Created on Thu Oct 23 10:13:19 2025

@author: narag
"""
import json
import os
import pandas as pd
import datetime
import zipfile
import math

############################################################################################
###########################             GLOBAL VALUES          #############################
############################################################################################
string_separator = "_"   #G2-Aluno3_p4-2023-12-04-161603.txt -->  G2-Aluno3
seting_separator_exclude = "." 

colunas_leq = ['device','measurement','x','y','z','duracao', 'Date','Time','LAeq(1s)', 'leq_16','leq_20','leq_25',
               'leq_31.5','leq_40','leq_50','leq_63','leq_80','leq_100', 'leq_125', 'leq_160', 'leq_200', 'leq_250', 
               'leq_315', 'leq_400', 'leq_500', 'leq_630', 'leq_800', 'leq_1000', 'leq_1250', 'leq_1600', 'leq_2000', 'leq_2500',  
               'leq_3150', 'leq_4000','leq_5000', 'leq_6300', 'leq_8000', 'leq_10000', 'leq_12500', 'leq_16000','leq_20000']

colunas_leq2 = colunas_leq.copy()  # copia a lista original
colunas_leq2.extend(["LA50", "LA50_1kHz"])

#path_ = os.getcwd() 
#filepath = path_ + "/test"

############################################################################################
###########################             NOISE CAPTURE          #############################
############################################################################################

def utc_to_hora(time_in_millis):
    # TRANSFORMING THE UTC TIME FORMAT 
    time_in_millis_br = time_in_millis - 10800000 #diferença entre UTC e fuso horario brasilia
    dt = datetime.datetime.fromtimestamp(time_in_millis_br / 1000.0, tz=datetime.timezone.utc)
    hora_utc = str(dt).split(" ")[1]     #15:04:57.609000+00:00
    hora = str(hora_utc).split(".")[0]   #15:04:57 
    date = dt.strftime("%d/%m/%y")
    
    return date, hora

def extract_zip(zip_file):
    # Função para extrair o conteúdo do arquivo geojson de um zip e retorná-lo
    with zipfile.ZipFile(zip_file) as zip_ref:
        with zip_ref.open('track.geojson') as geojson_file:
            
            return geojson_file.read().decode('utf-8')

def extract_geojson(geojson_file, arquivo):
    # EXTRACT DATA FROM GEOJSON 
    # INPUT: Nome do arquivo com seu caminho completo, em formato .geojson
    global string_separator 
    global seting_separator_exclude
    
    legend  = os.path.basename(arquivo)
    colunas_noisecapture = ['device','measurement','x', 'y', 'z', 'accuracy', 'speed', 'Date', 'Time', 'LAeq(1s)',
               'leq_100', 'leq_125', 'leq_160', 'leq_200', 'leq_250', 'leq_315',
               'leq_400', 'leq_500', 'leq_630', 'leq_800', 'leq_1000', 'leq_1250',
               'leq_1600', 'leq_2000', 'leq_2500', 'leq_3150', 'leq_4000', 'leq_5000',
               'leq_6300', 'leq_8000', 'leq_10000', 'leq_12500', 'leq_16000']
    
    df_geojson = pd.DataFrame(columns=colunas_noisecapture)  
    for feature in geojson_file['features']:
        lista = []
        lista.append(legend.split(string_separator)[0]) #device
        lista.append(legend.split(string_separator)[1].split(seting_separator_exclude)[0] )  #measurement
        
        # INFORMAÇÕES DE LOCALIZAÇÃO
        if feature['geometry']:
            lista.append(feature['geometry']['coordinates'][0]) #X
            lista.append(feature['geometry']['coordinates'][1]) #Y
            if len(feature['geometry']['coordinates']) > 2:
                lista.append(feature['geometry']['coordinates'][2]) #Z
            else:
                lista.append("none") #Z   
        else:
            lista.append("none") #X
            lista.append("none") #Y
            lista.append("none") #Z      
        lista.append(feature['properties']['accuracy'])
        if 'speed' in feature['properties']:
            lista.append(feature['properties']['speed']) #Z
        else:
            lista.append("none") #speed 
        
        Time, Date = utc_to_hora(feature['properties']['leq_utc'])  
        lista.append(Time) #Time
        lista.append(Date)  #day
        lista.append(feature['properties']['leq_mean'])
        for key in feature['properties']:
            if key.startswith('leq_') and key not in ['leq_id', 'leq_utc', 'leq_mean']:
                lista.append(feature['properties'][key])
                
        df_lista = pd.DataFrame([lista], columns = df_geojson.columns)  
        df_geojson = pd.concat([df_geojson, df_lista], ignore_index=True)
    
    df_geojson['duracao'] = len(df_geojson)

    return df_geojson

############################################################################################
###########################               OPENOISE             #############################
############################################################################################

def extract_openoise(arquivo, year): 
    # EXTRACT DATA FROM .TXT (global value only)
    # INPUT: Nome do arquivo com seu caminho completo, em formato .txt
    # default:
    global string_separator 
    global seting_separator_exclude
    global colunas_leq
    
    legend  = os.path.basename(arquivo)
    if year == "2023":
        df_measure = pd.read_csv(arquivo,sep=';',decimal='.',header=0) 
        df_measure['calibration'] = None
        df_measure['x'] = None
        df_measure['y'] = None
        df_measure['z'] = None
    elif year == "2024":
        calibration_value = None
        x = None
        y = None
        z = None
        with open(arquivo, 'r') as f:
            for i, line in enumerate(f):
                if line.startswith("Calibration:"):
                    calibration_value = line.split(':')[1].strip().split(' dB')[0]  # Extrair o valor da calibração
                elif line.startswith("Coordinates:"):
                    x = line.split(':')[1].strip().strip().split(',')[1] 
                    y = line.split(':')[1].strip().strip().split(',')[0] 
                elif line.startswith("Date"): # Abrir o arquivo para encontrar a linha que começa com "Date"
                    skiprows = i  # Definir o número de linhas a pular
                    print(i)
                    break
        # Ler o arquivo CSV a partir da linha que começa com "Date"
        df_measure = pd.read_csv(arquivo, sep=';', decimal='.', skiprows=skiprows,header=0 ) 
        df_measure['calibration'] = calibration_value
        df_measure['x'] = x
        df_measure['y'] = y
        df_measure['z'] = z
    
    # corrigir dados numéricos que são lidos como string
    for i, column in enumerate(df_measure.columns):
        if column in ['Date', 'Time', 'Marker']:
            continue  # Pula as duas primeiras colunas, a quinta coluna e 'Time' 
        df_measure[column] = df_measure[column].apply(lambda x: str(x).replace(',', '.') if isinstance(x, str) else x)
        df_measure[column] = pd.to_numeric(df_measure[column], errors='coerce')
        
    # adicionando colunas padrão
    device = legend.split(string_separator)[0]
    measurement = legend.split(string_separator)[1].split(seting_separator_exclude)[0]
    df_measure["device"] = device
    df_measure["measurement"] = measurement
    df_measure["duracao"] = len(df_measure.index)
    
    # Excluindo colunas desnecessárias e adicionado quando não tem a informação da frequência
    if 'LZeq(t)' in df_measure.columns:
        colunas_para_excluir = ['LAeq(t)'] + ['LZeq(t)'] + ['LZeq(1s)'] + [coluna for coluna in df_measure.columns if coluna.startswith('LZmin_')]
        df_measure = df_measure.drop(columns=colunas_para_excluir)
        df_measure.columns = df_measure.columns.str.replace('LZeq_', 'leq_')
    elif 'LZeq(t)' not in df_measure.columns:
        for col in colunas_leq[9:]:
            df_measure[col] = 0
        df_measure['leq_1000'] = df_measure['LAeq(1s)']
    
    return df_measure

############################################################################################
##########################           PROCESSING  LAeq          #############################
############################################################################################

def calculate_LAEQmean(df):
    # Calcula a média logarítmica (LAEQ) para cada coluna numérica (flota64) de um DataFrame
    #INPUT --> df : pandas.DataFrame
    #output --> laeq_mean_series : pandas.Series  
    mean_list = [df['device'].iloc[0], df['measurement'].iloc[0],
                 df['x'].iloc[4],df['y'].iloc[4],df['z'].iloc[4],
                 df['duracao'].iloc[0],  df['Date'].iloc[0],df['Time'].iloc[0]]

    for col in df:
        if col.startswith("leq_") or col =='LAeq(1s)':
            valores = df[col].dropna()
            if not valores.empty:
                soma_valores = (10 ** (valores / 10)).sum()
                valor = 10 * math.log10(soma_valores / len(valores))
            else:
                valor = None
            mean_list.append(valor)

    return mean_list

# analyze_time_domain
def calculate_LAEQmean_general(df):
    mean_list = []

    for col in df:
        if col != "Time":
            valores = df[col].dropna()
            if not valores.empty:
                soma_valores = (10 ** (valores / 10)).sum()
                valor = 10 * math.log10(soma_valores / len(valores))
            else:
                valor = None
            mean_list.append(valor)

    return mean_list

def filtro_A(df):
    # Definir as colunas de frequências e os valores de correção
    freq_columns = ['leq_16', 'leq_20', 'leq_25', 'leq_31.5', 'leq_40', 'leq_50', 
                    'leq_63', 'leq_80', 'leq_100', 'leq_125', 'leq_160', 'leq_200', 
                    'leq_250', 'leq_315', 'leq_400', 'leq_500', 'leq_630', 'leq_800', 
                    'leq_1000', 'leq_1250', 'leq_1600', 'leq_2000', 'leq_2500', 
                    'leq_3150', 'leq_4000', 'leq_5000', 'leq_6300', 'leq_8000', 
                    'leq_10000', 'leq_12500', 'leq_16000', 'leq_20000']
    
    correction = [-56.7, -50.5, -44.7, -39.4, -34.6, -30.2, -26.2, -22.5, -19.1, 
                -16.1, -13.3, -10.9, -8.6, -6.6, -4.8, -3.2, -1.9, -0.8, 0, 
                0.6, 1, 1.2, 1.3, 1.2, 1, 0.5, -0.1, -1.1, -2.5, -4.3, -6.6, -9.3]

    for col, cor in zip(freq_columns, correction):
        df[col] = df[col] + cor
    
    return df

############################################################################################
##########################              TIME DOMAIN            #############################
############################################################################################

def devices_time_domain(arquivos, year, descriptor, output_name = None, save_file = None):
    
    # Empty list to store DataFrames
    dfs = []
    if descriptor == "LAeq":
        descriptor_column = 'LAeq(1s)'
    elif descriptor == "1kHz":
        descriptor_column = 'leq_1000'

    # Loop through each file in arquivos
    for arquivo in arquivos:
        legend  = os.path.basename(arquivo)  # Get the filename
        if arquivo.endswith('.zip'):
            geojson_content = extract_zip(arquivo)
            geojson = json.loads(geojson_content)  # Carregar o conteúdo extraído como JSON
            df = extract_geojson(geojson, legend)
            dfs.append(df[['Time', descriptor_column]].rename(columns={descriptor_column: legend}))         
        elif arquivo.endswith('.geojson'):  
            with open(arquivo, 'r') as f:
                geojson = json.load(f)
                df = extract_geojson(geojson, legend)
                dfs.append(df[['Time', descriptor_column]].rename(columns={descriptor_column: legend}))          
        elif arquivo.endswith('.txt'):
            df = extract_openoise(arquivo, year)
            dfs.append(df[['Time', descriptor_column]].rename(columns={descriptor_column: legend}))                
        elif arquivo.endswith('.xlsx'):
            try:
                df = pd.read_excel(arquivo, sheet_name="Time History", header=0)
                if descriptor == "LAeq":
                    if 'LAeq' in df.columns:
                        df = df.rename(columns={'LAeq': 'LAeq(1s)'})
                    dfs.append(df[['Time', 'LAeq(1s)']].rename(columns={'LAeq(1s)': legend}))
                elif descriptor == "1kHz":
                    dfs.append(df[['Time', '1/3 LZF 1000']].rename(columns={'1/3 LZF 1000': legend}))
            except ValueError:
                continue
    
    # Convert 'Time' column to datetime for all DataFrames
    for i in range(len(dfs)):
        dfs[i]['Time'] = pd.to_datetime(dfs[i]['Time'], format='%H:%M:%S', errors='coerce').dt.time
    
    # Merge DataFrames based on 'Time' column
    merged_df = dfs[0]
    for df in dfs[1:]:
        merged_df = pd.merge(merged_df, df, on='Time', how='outer')
    merged_df = merged_df.sort_values(by='Time')
    
    if save_file == "yes":
        merged_df.to_excel(output_name + ".xlsx",sheet_name='time_domain',index=False)

    return merged_df

############################################################################################
########################             FREQUENCY DOMAIN           ############################
############################################################################################

def read_frequency_domain(filepath, year, output_name = None, save_file = None):
    #empty list to add the Dataframes
    global colunas_leq

    arquivos = [os.path.join(filepath, arquivo) for arquivo in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, arquivo))]
    dfs = [] 

    for arquivo in arquivos:
        legend  = os.path.basename(arquivo)
        if arquivo.endswith('.txt'): 
            # read file
            df = extract_openoise(arquivo, year)
            # preparing the file
            df = df[colunas_leq]
            df = df[df['leq_1000'] != 0] 
            # Applying the function
            df = filtro_A(df)
            LA50 = df["LAeq(1s)"].median()
            LA50_1kHz = df["leq_1000"].median()            
            mean_values = calculate_LAEQmean(df)  # Calculate the energetic mean of each column
            mean_values.append(LA50)  # Add LA50 at the end
            mean_values.append(LA50_1kHz) 
            dfs.append(mean_values)   
        elif arquivo.endswith('.zip'):
            # read file
            geojson_content = extract_zip(arquivo)
            geojson = json.loads(geojson_content)  # Carregar o conteúdo extraído como JSON
            df = extract_geojson(geojson, legend)
            # preparing the file
            df = df.assign(**{coluna: 0 for coluna in ['leq_16', 'leq_20', 'leq_25', 'leq_31.5', 'leq_40', 'leq_50', 'leq_63', 'leq_80', 'leq_20000']})
            #df = df.drop(columns=['x', 'y', 'z', 'accuracy', 'speed'])
            df = df[colunas_leq]
            df = df[df['leq_1000'] != 0] 
            # Applying the function
            LA50 = df["LAeq(1s)"].median()
            LA50_1kHz = df["leq_1000"].median()
            mean_values = calculate_LAEQmean(df)  # Calculate the energetic mean of each column
            mean_values.append(LA50)  # Add LA50 at the end
            mean_values.append(LA50_1kHz) 
            dfs.append(mean_values)  
        elif arquivo.endswith('.geojson'):  
            with open(arquivo, 'r') as f:
                # read file
                geojson = json.load(f)
                df = extract_geojson(geojson, legend)
                # preparing the file
                df = df.assign(**{coluna: 0 for coluna in ['leq_16', 'leq_20', 'leq_25', 'leq_31.5', 'leq_40', 'leq_50', 'leq_63', 'leq_80', 'leq_20000']})
                df = df[colunas_leq]
                df = df[df['leq_1000'] != 0] 
                # Applying the function
                LA50 = df["LAeq(1s)"].median()
                LA50_1kHz = df["leq_1000"].median()
                mean_values = calculate_LAEQmean(df)  
                mean_values.append(LA50) 
                mean_values.append(LA50_1kHz) 
                dfs.append(mean_values)   
        elif arquivo.endswith('.xlsx'): 
            try:
                df = pd.read_excel(arquivo, sheet_name="Time History", header=0)
                # preparing the file
                device = legend.split(string_separator)[0]
                measurement = legend.split(string_separator)[1].split(seting_separator_exclude)[0]
                df["device"] = device
                df["measurement"] = measurement
                df["duracao"] = len(df.index)
                # rename columns to adjust to the pattern
                df.columns = df.columns.str.replace('1/3 LZeq ', 'leq_', regex=False) 
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
                if 'Time' in df.columns:
                    if isinstance(df['Time'].iloc[0], datetime.time):  
                        df['Time'] = df['Time'].apply(lambda x: x.strftime('%H:%M:%S') if pd.notnull(x) else None)
                    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S', errors='coerce').dt.strftime('%H:%M:%S')
                df.rename(columns={'leq_16.0': 'leq_16','leq_20.0': 'leq_20','leq_25.0': 'leq_25',
                'leq_40.0': 'leq_40','leq_50.0': 'leq_50','leq_63.0': 'leq_63','leq_80.0': 'leq_80'}, inplace=True)
                df = df.rename(columns={'LAeq': 'LAeq(1s)'})
                df['x'] = None
                df['y'] = None
                df['z'] = None
                df = df[colunas_leq]       
                #Aplicando a função
                df = filtro_A(df)
                LA50 = df["LAeq(1s)"].median()
                LA50_1kHz = df["leq_1000"].median()            
                mean_values = calculate_LAEQmean(df)  
                mean_values.append(LA50)  
                mean_values.append(LA50_1kHz) 
                dfs.append(mean_values)  
            except ValueError:
                continue
            
    merged_df = pd.DataFrame(dfs, columns=colunas_leq2)
    if save_file == "yes":
        merged_df.to_excel(os.path.join(filepath, f"{output_name}.xlsx"),index=False)

    return merged_df