"""
Created on Tue July 16 17:07:00 2023

@author: danikam
"""

import pandas as pd

from CommonTools import get_top_dir, mergeShapefile, saveShapefile
import os

G_PER_LB = 453.592
KWH_PER_MWH = 1000


def read_iso_emissions_data(top_dir, hour):
    """
    Reads in grid emission intensities by ISO from https://www.electricitymaps.com/data-portal (processed by Noman Bashir)

    Parameters
    ----------
    top_dir (string): path to the top level of the git repo

    Returns
    -------
    iso_emissions_data_df (pd.DataFrame): Dataframe containing the emissions data for each US ISO, converted from units of gCO2eq / kWh to lb CO2eq / MWh
    """
    columns = ["zoneName", "mean", "std_up", "std_down"]

    data_df = pd.DataFrame(columns=columns)

    # Read in the data associated with each eGrids subregion
    dataDir = f"{top_dir}/data/daily_carbon_intensity_data_usa"
    for filename in os.listdir(dataDir):
        filepath = os.path.join(dataDir, filename)

        # Confirm that it's a file and not a directory
        if os.path.isfile(filepath) and filename.endswith(".csv"):
            data_iso_df = pd.read_csv(filepath)
            row_dict = {"zoneName": filename.split("_")[0]}

            row_dict["mean"] = data_iso_df["mean"].iloc[hour] * KWH_PER_MWH / G_PER_LB
            row_dict["std_up"] = (
                (data_iso_df["mean"].iloc[hour] + data_iso_df["std"].iloc[hour])
                * KWH_PER_MWH
                / G_PER_LB
            )
            row_dict["std_down"] = (
                (data_iso_df["mean"].iloc[hour] - data_iso_df["std"].iloc[hour])
                * KWH_PER_MWH
                / G_PER_LB
            )

            # Convert row_dict to a DataFrame
            new_row_df = pd.DataFrame([row_dict])

            # Append new_row_df to data_df
            data_df = pd.concat([data_df, new_row_df], ignore_index=True)

    return data_df
    
def read_average_iso_emissions(top_dir):
    """
    Reads in grid emission intensities by ISO from https://www.electricitymaps.com/data-portal (processed by Noman Bashir) and gets the average value over all rows

    Parameters
    ----------
    top_dir (string): path to the top level of the git repo

    Returns
    -------
    iso_emissions_data_df (pd.DataFrame): Dataframe containing the emissions data for each US ISO, converted from units of gCO2eq / kWh to lb CO2eq / MWh
    """
    columns = ["zoneName", "mean"]

    data_df = pd.DataFrame(columns=columns)

    # Read in the data associated with each eGrids subregion
    dataDir = f"{top_dir}/data/daily_carbon_intensity_data_usa"
    for filename in os.listdir(dataDir):
        filepath = os.path.join(dataDir, filename)

        # Confirm that it's a file and not a directory
        if os.path.isfile(filepath) and filename.endswith(".csv"):
            data_iso_df = pd.read_csv(filepath)
            row_dict = {"zoneName": filename.split("_")[0]}
            
            row_dict["mean"] = data_iso_df["mean"].mean() * KWH_PER_MWH / G_PER_LB

            # Convert row_dict to a DataFrame
            new_row_df = pd.DataFrame([row_dict])
            print(new_row_df)

            # Append new_row_df to data_df
            data_df = pd.concat([data_df, new_row_df], ignore_index=True)
    
    print(data_df)
    return data_df


def main():
    # Get the path to the top level of the Git repo
    top_dir = get_top_dir()

#    for hour in range(24):
#        # Read in ISO emission rate data for the given hour in 2022
#        iso_emissions_data = read_average_iso_emissions_data(top_dir, hour)
#
#        # Merge the ISO emission rate data for 2022 with the shapefile containing borders for the data source
#        merged_dataframe_iso_emissions = (
#            mergeShapefile(
#                iso_emissions_data, f"{top_dir}/data/world.geojson", "zoneName"
#            )
#            .dropna()
#            .drop(columns=["countryKey", "countryName"])
#        )
#
#        saveShapefile(
#            merged_dataframe_iso_emissions,
#            f"{top_dir}/data/daily_grid_emission_profiles/daily_grid_emission_profile_hour{hour}.shp",
#        )
    
    # Read in ISO emission rate data for 2022
    iso_emissions_data = read_average_iso_emissions(top_dir)

    # Merge the ISO emission rate data for 2022 with the shapefile containing borders for the data source
    merged_dataframe_iso_emissions = (
        mergeShapefile(
            iso_emissions_data, f"{top_dir}/data/world.geojson", "zoneName"
        )
        .dropna()
        .drop(columns=["countryKey", "countryName"])
    )

    saveShapefile(
        merged_dataframe_iso_emissions,
        f"{top_dir}/data/hourly_grid_emissions/average_grid_emissions.shp",
    )


main()
