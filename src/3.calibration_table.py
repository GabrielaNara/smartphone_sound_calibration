import pandas as pd
import os
path_ = os.getcwd() 

path_ = os.getcwd() 
path_ = path_.split("\\src")[0]

############################################################################################
#############################              INPUT            ################################
############################################################################################

# CHOOSE INPUT
descriptor = "LAeq" #CHOOSE BETWEEN "1Khz" or "Laeq"
locations = ['p1','p2'] #Insert the name of locationbs to consider 

# DEFAULT PARAMETERS
df_TABLE =  pd.read_excel(path_ + "/input.xlsx",sheet_name="mobile_sensors") #path where to find the inputs

############################################################################################
######################                  PROCESSING              ############################
############################################################################################

def search_value(df, device, column):
    resultado = df[df['device'] == device]
    if not resultado.empty:
        return resultado[column].values[0] * (-1)
    else:
        return None
    
comparison_values = ["LAeq","LA50"]
for comp in comparison_values:
    for loc in locations:
        df_loc = pd.read_excel(path_ + f"/outputs/time_series_by_sensor/__delta_{loc}_{descriptor}.xlsx")
        df_loc['device'] = df_loc['device'].apply(lambda x: x.split('_')[0])      
        
        col_name = f"bias_{loc}_{comp}"
        df_TABLE[col_name] = None

        for index, row in df_TABLE.iterrows():
            device = row['device']
            df_TABLE.at[index, col_name] = search_value(
                df_loc, device, f'Δ_{comp}'
            )

        df_TABLE[col_name] = pd.to_numeric(df_TABLE[col_name], errors='coerce')
        
    # Bias and range for all points    
    cols = [f"bias_{loc}_{comp}" for loc in locations]
    df_TABLE[f'bias_{comp}'] = df_TABLE[cols].mean(axis=1)
    
    valid = df_TABLE[cols].count(axis=1)
    df_TABLE[f'range_{comp}'] = df_TABLE[cols].max(axis=1) - df_TABLE[cols].min(axis=1)
    df_TABLE.loc[valid <= 1, f'range_{comp}'] = None  # ou np.nan

# Save the result to Excel
df_TABLE.to_excel(path_+f"/outputs/calibration_table.xlsx",index=False)