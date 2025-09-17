import xarray as xr

# --- Configuration ---
NC_FILE_PATH = '20240101_prof.nc'

try:
    print(f"--- Inspecting variables in: {NC_FILE_PATH} ---\n")
    with xr.open_dataset(NC_FILE_PATH) as ds:
        print("## Dimensions:")
        for dim in ds.dims:
            print(f"- {dim} (size: {ds.dims[dim]})")
        
        print("\n## Coordinates:")
        for coord in ds.coords:
            print(f"- {coord}")

        print("\n## Data Variables:")
        for var in ds.data_vars:
            print(f"- {var}")

except FileNotFoundError:
    print(f"Error: File not found at '{NC_FILE_PATH}'. Make sure it's in the correct directory.")
except Exception as e:
    print(f"An error occurred while reading the file: {e}")