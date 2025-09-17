import xarray as xr
import pandas as pd
from sqlalchemy import create_engine
import os
import glob

# --- Configuration ---
DB_FILE_PATH = 'argo.db'
NC_FILE_PATTERN = '*.nc' # Pattern to find all NetCDF files

def main():
    """
    Main function to process NetCDF files and store them in an SQLite database.
    This version now processes all .nc files in the directory.
    """
    nc_files = glob.glob(NC_FILE_PATTERN)
    if not nc_files:
        print(f"❌ Error: No data files found matching '{NC_FILE_PATTERN}'")
        return

    print(f"➡️ Found {len(nc_files)} NetCDF files to process.")
    
    all_dfs = []
    for nc_file in nc_files:
        print(f"➡️ Loading NetCDF dataset from '{nc_file}'...")
        try:
            ds = xr.open_dataset(nc_file, decode_times=True)
            
            # --- Define Correct Variable Names ---
            time_var = 'JULD'
            lat_var = 'LATITUDE'
            lon_var = 'LONGITUDE'
            pres_var = 'PRES_ADJUSTED'
            temp_var = 'TEMP_ADJUSTED'
            sal_var = 'PSAL_ADJUSTED'
            float_id_var = 'PLATFORM_NUMBER'
            
            print("➡️ Manually constructing DataFrame from profile data...")
            df = ds[[pres_var, temp_var, sal_var]].to_dataframe()
            
            profile_meta_vars = [time_var, lat_var, lon_var, float_id_var]
            df_meta = ds[profile_meta_vars].to_dataframe()

            df_full = pd.merge(df, df_meta, on='N_PROF', how='left')
            df_full = df_full.reset_index()

            print("➡️ Processing and cleaning data...")

            rename_map = {
                'N_PROF': 'profile_id',
                pres_var: 'PRES',
                temp_var: 'TEMP',
                sal_var: 'PSAL',
                lat_var: 'LATITUDE',
                lon_var: 'LONGITUDE',
                float_id_var: 'float_id',
                time_var: 'TIME'
            }
            df_final = df_full.rename(columns=rename_map)

            df_final['float_id'] = df_final['float_id'].astype(str)

            required_columns = ['float_id', 'PRES', 'TEMP', 'PSAL', 'LATITUDE', 'LONGITUDE', 'TIME', 'profile_id']
            df_final = df_final[required_columns].dropna()
            
            if not df_final.empty:
                all_dfs.append(df_final)
            else:
                print(f"⚠️ Warning: No data extracted from {nc_file}.")

        except Exception as e:
            print(f"❌ Error processing {nc_file}: {e}")
            continue

    if not all_dfs:
        print("❌ Error: After processing all files, no data was available.")
        return
        
    combined_df = pd.concat(all_dfs, ignore_index=True)

    print(f"➡️ Storing {len(combined_df)} total measurements into SQLite database at '{DB_FILE_PATH}'...")
    engine = create_engine(f'sqlite:///{DB_FILE_PATH}')
    combined_df.to_sql('profiles', engine, if_exists='replace', index=False)

    print("\n✅ Success! Database 'argo.db' has been created with data from all files.")
    print("\nSample of the stored data:")
    print(combined_df.head())


if __name__ == '__main__':
    main()