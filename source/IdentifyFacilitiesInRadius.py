#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 28 17:34:00 2023

@author: danikam
"""

# Import needed modules

import pandas as pd

import geopandas as gpd
import argparse
from CommonTools import get_top_dir, saveShapefile
import os


def miles_to_meters(d_miles):
    """
    Reads in a distance in miles and converts it to meters

    Parameters
    ----------
    d_miles (float): Distance in miels

    Returns
    -------
    d_meters (float): Distance in meters
    """

    d_meters = d_miles * 1600
    return d_meters


def make_circle(center_long, center_lat, radius):
    """
    Reads in a longitude and latitude, and makes a shapefile object representing a circle of the given radius.

    Parameters
    ----------
    center_long (double): Longitude of the center of the circle
    center_lat (double): Latitude of the center of the circle
    radius (double): Radius of the circle (in miles)

    Returns
    -------
    gpd_circle (gpd.DataFrame): Geodataframe with the boundary of a circle centered at (center_long, center_lat) with the given radius.
    """

    df_data = pd.DataFrame(
        {
            "Latitude": [center_lat],
            "Longitude": [center_long],
        }
    )

    gpd_center = gpd.GeoDataFrame(
        df_data,
        geometry=gpd.points_from_xy(df_data.Longitude, df_data.Latitude),
        crs="EPSG:4326",
    )

    # Convert to projected coordinate system to evaluate a circle of a given radius around the central coordinates
    gpd_center = gpd_center.to_crs("EPSG:3857")

    # Convert the given radius to meters
    radius_meters = miles_to_meters(radius)

    # Make a circle fo the given radius around the central coordinates
    gpd_circle = gpd_center.buffer(radius_meters)

    # Convert back to the geographic coordinate system
    return gpd_circle.to_crs("EPSG:4326")


def identify_points_in_circle(gpd_circle, gpd_points):
    """
    Identifies points belonging to gpd_points within the circle with bounded by gpd_circle.

    Parameters
    ----------
    gpd_circle (gpd.DataFrame): Geopandas dataframe containing the circle to find points within
    gpd_points (gpd.DataFrame): Geopandas dataframe containing the points to be identified within the circle

    Returns
    -------
    gpd_points_in_circle (gpd.DataFrame): Geodataframe with the points identified within the circle.
    """

    # Convert the circle from a polygon to a GeoPandas dataframe
    gdf_circle = gpd.GeoDataFrame(geometry=gpd_circle, crs="EPSG:4326")
    gpd_points = gpd_points.to_crs("EPSG:4326")
    gpd_points_in_circle = gpd.sjoin(gpd_points, gdf_circle)

    return gpd_points_in_circle


def make_readme(center_long, center_lat, radius, name="default"):
    """
    Make a README to document the circle info

    Parameters
    ----------
    center_long (double): Longitude of the center of the circle
    center_lat (double): Latitude of the center of the circle
    radius (double): Radius of the circle
    name (string): Name of the circle

    Returns
    -------
    None
    """

    top_dir = get_top_dir()

    # Make a README indicating the central coordinates, radius, and name of the circle
    info = f"Circle name: {name} \nCentral coordinates: ({center_lat}, {center_long}) \nCircle radius: {radius} miles \nShapefiles can be found in: {top_dir}/data/facilities_in_circle_{name}/shapefiles \nInfo for facilities located in circle can be found in: {top_dir}/data/facilities_in_circle_{name}/facilities_in_circle.xlsx"
    f_readme = open(f"{top_dir}/data/facilities_in_circle_{name}/README.md", "w")
    f_readme.write(info)


def make_info_table(dict_output, name="default"):
    """
    Makes an excel spreadsheet with the relevant info for each facility in the circle

    Parameters
    ----------
    dict_output (dictionary of gpd.DataFrame): Dictionary containing the geopandas dataframes for each set of points contained within the circle.

    Returns
    -------
    None
    """

    top_dir = get_top_dir()

    with pd.ExcelWriter(
        f"{top_dir}/data/facilities_in_circle_{name}/facilities_in_circle.xlsx"
    ) as writer:
        for key in dict_output:
            gpd_output = dict_output[key]

            # Add longitude and latitude if needed
            if "Latitude" not in gpd_output.columns:
                gpd_output["Latitude"] = gpd_output.geometry.y
            if "Longitude" not in gpd_output.columns:
                gpd_output["Longitude"] = gpd_output.geometry.x

            # Remove unneeded columns
            gpd_output = gpd_output.drop(["geometry", "index_right"], axis=1)
            if "OBJECTID" in gpd_output.columns:
                gpd_output = gpd_output.drop(["OBJECTID"], axis=1)
            if "State_numb" in gpd_output.columns:
                gpd_output = gpd_output.drop(["State_numb"], axis=1)
            if "" in gpd_output.columns:
                gpd_output = gpd_output.drop([""], axis=1)

            # Save to the file
            gpd_output.to_excel(writer, sheet_name=key, index=False)


parser = argparse.ArgumentParser()
parser.add_argument("-a", "--latitude", default=33, type=float)
parser.add_argument("-o", "--longitude", default=-97, type=float)
parser.add_argument("-r", "--radius", default=600, type=float)
parser.add_argument("-n", "--name", default="default")


def main():
    # Get the command-line arguments
    args = parser.parse_args()

    # Get the path to the top level of the Git repo
    top_dir = get_top_dir()

    # Get the hydrogen electrolyzer facilities
    gpd_electrolyzer_planned = gpd.read_file(
        f"{top_dir}/data/hydrogen_hubs/shapefiles/electrolyzer_planned_under_construction.shp"
    )
    gpd_electrolyzer_installed = gpd.read_file(
        f"{top_dir}/data/hydrogen_hubs/shapefiles/electrolyzer_installed.shp"
    )
    gpd_electrolyzer_operational = gpd.read_file(
        f"{top_dir}/data/hydrogen_hubs/shapefiles/electrolyzer_operational.shp"
    )

    # Get the hydrogen refinery facilities
    gpd_refinery = gpd.read_file(
        f"{top_dir}/data/hydrogen_hubs/shapefiles/refinery.shp"
    )

    # Get truck stop parking data
    gpd_truck_stop = gpd.read_file(
        f"{top_dir}/data/Truck_Stop_Parking/Truck_Stop_Parking.shp"
    )

    # Make a circle of the given radius
    gpd_circle = make_circle(args.longitude, args.latitude, args.radius)

    gpd_electrolyzer_planned_in_circle = identify_points_in_circle(
        gpd_circle, gpd_electrolyzer_planned
    )
    gpd_electrolyzer_installed_in_circle = identify_points_in_circle(
        gpd_circle, gpd_electrolyzer_installed
    )
    gpd_electrolyzer_operational_in_circle = identify_points_in_circle(
        gpd_circle, gpd_electrolyzer_operational
    )

    gpd_refinery_in_circle = identify_points_in_circle(gpd_circle, gpd_refinery)

    gpd_truck_stop_in_circle = identify_points_in_circle(gpd_circle, gpd_truck_stop)

    dir = f"{top_dir}/data/facilities_in_circle_{args.name}/shapefiles"
    if not os.path.exists(dir):
        os.makedirs(dir)

    saveShapefile(
        gpd_electrolyzer_planned_in_circle,
        f"{top_dir}/data/facilities_in_circle_{args.name}/shapefiles/electrolyzer_planned_under_construction.shp",
    )
    saveShapefile(
        gpd_electrolyzer_installed_in_circle,
        f"{top_dir}/data/facilities_in_circle_{args.name}/shapefiles/electrolyzer_installed.shp",
    )
    saveShapefile(
        gpd_electrolyzer_operational_in_circle,
        f"{top_dir}/data/facilities_in_circle_{args.name}/shapefiles/electrolyzer_operational.shp",
    )
    saveShapefile(
        gpd_refinery_in_circle,
        f"{top_dir}/data/facilities_in_circle_{args.name}/shapefiles/refinery.shp",
    )
    saveShapefile(
        gpd_truck_stop_in_circle,
        f"{top_dir}/data/facilities_in_circle_{args.name}/shapefiles/Truck_Stop_Parking.shp",
    )

    saveShapefile(
        gpd_circle,
        f"{top_dir}/data/facilities_in_circle_{args.name}/shapefiles/circle.shp",
    )

    # Make a README with the relevant info
    make_readme(args.longitude, args.latitude, args.radius, name="default")

    dict_output = {
        "H2 Elec (Planned)": gpd_electrolyzer_planned_in_circle,
        "H2 Elec (Installed)": gpd_electrolyzer_installed_in_circle,
        "H2 Elec (Operational)": gpd_electrolyzer_operational_in_circle,
        "H2 from Ref": gpd_refinery_in_circle,
        "Truck stops": gpd_truck_stop_in_circle,
    }

    make_info_table(dict_output)


main()
