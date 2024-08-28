#!/usr/bin/env python3

"""
Created on Mon Mar 27 10:28:00 2023
@author: danikam
"""

# Import needed modules
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import InfoObjects
from ViusTools import (
    make_aggregated_df,
    add_GREET_class,
    add_payload,
    get_annual_ton_miles,
    make_basic_selections,
    get_key_from_value,
    divide_mpg_by_10,
)
from CommonTools import get_top_dir
from scipy.stats import gaussian_kde

matplotlib.rc("xtick", labelsize=18)
matplotlib.rc("ytick", labelsize=18)

# Conversion from pounds to tons
LB_TO_TONS = 1 / 2000.0

# Get the path to the top level of the git repo
top_dir = get_top_dir()

######################################### Functions defined here ##########################################


def get_commodity_pretty(commodity="all"):
    """
    Gets a human-readable name of the input commodity column name, using the mapping specified in the dictionary pretty_commodities_dict

    Parameters
    ----------
    commodity (string): Column name of the given commodity

    Returns
    -------
    commodity_pretty (string): Human-readable version of the input column name

    NOTE: None.
    """
    if commodity == "all":
        commodity_pretty = "All commodities"
    else:
        commodity_pretty = InfoObjects.pretty_commodities_dict[commodity]
    return commodity_pretty


def get_region_pretty(region="US"):
    """
    Gets a human-readable name of the input column name associated with the truck's administrative state or region (a.k.a. region), using the mapping specified in the dictionary states_dict

    Parameters
    ----------
    region (string): Column name of the given administrative state or region

    Returns
    -------
    region_pretty (string): Human-readable version of the input column name

    NOTE: None.
    """
    if region == "US":
        region_pretty = "US"
    else:
        region_pretty = InfoObjects.states_dict[region]
    return region_pretty


def get_range_pretty(truck_range="all"):
    """
    Gets a human-readable name of the input column name associated with the truck's trip range window, using the mapping specified in the dictionary pretty_range_dict

    Parameters
    ----------
    truck_range (string): Column name of the given trip range window

    Returns
    -------
    range_pretty (string): Human-readable version of the input column name

    NOTE: None.
    """
    if truck_range == "all":
        range_pretty = "All Ranges"
    else:
        range_pretty = InfoObjects.pretty_range_dict[truck_range]
    return range_pretty


def print_all_commodities(df):
    """
    Prints out the number of samples of each commodity in the VIUS, as well as the total number of commodities

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    Returns
    -------
    None

    NOTE: None.
    """
    n_comm = 0
    for column in df:
        if column.startswith("P") and not column.startswith("P_"):
            n_column = len(df[~df[column].isna()][column])
            print(f"Total number of samples for commodity {column}: {n_column}")
            n_comm += 1
    print(f"Total number of commodities: {n_comm}\n\n")


def print_all_states(df):
    """
    Prints out the number of samples for each state in the VIUS, as well as the total number of samples

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    Returns
    -------
    None

    NOTE: None.
    """
    n_samples = 0
    for state in range(1, 57):
        if state not in InfoObjects.states_dict:
            continue
        n_state = len(
            df[(~df["ADM_STATE"].isna()) & (df["ADM_STATE"] == state)]["ADM_STATE"]
        )
        state_str = InfoObjects.states_dict[state]
        print(f"Total number of samples in {state_str}: {n_state}")
        n_samples += n_state
    print(f"total number of samples: {n_samples}\n\n")


def plot_greet_class_hist(
    df,
    commodity="all",
    truck_range="all",
    region="US",
    range_threshold=0,
    commodity_threshold=0,
    set_commodity_title="default",
    set_commodity_save="default",
    set_range_title="default",
    set_range_save="default",
    aggregated=False,
    weight_by_tm=True,
):
    """
    Calculates and plots the distributions of GREET class and fuel type for different commodities ('commmodity' parameter), trip range windows ('truck_range' parameter), and administrative states ('region' parameter). Samples used to produce the distributions are weighted by the average annual ton-miles reported carrying the given 'commodity' over the given 'truck_range', for the given administrative 'region'.

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    commodity (string): Name of the column of VIUS data containing the percentage of ton-miles carrying the given commodity

    truck_range (string): Name of the column of VIUS data containing the percentage of ton-miles carried over the given trip range

    region (string): Name of the column of VIUS data containing boolean data to indicate the truck's administrative state

    range_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the truck_range is not 'all'

    commodity_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the commodity is not 'all'

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted commodity to be shown in the plot title

    set_commodity_save (string): Allows the user to set the keyword for the plotted commodity to be included in the filenames of the saved plots

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted trip range to be shown in the plot title

    set_range_save (string): Allows the user to set the keyword for the plotted trip range to be included in the filenames of the saved plots

    aggregated (boolean): If set to True, adds an additional string '_aggregated' to the filenames of the saved plots to indicate that aggregation has been done to obtain common commodity and/or trip range definitions between FAF5 and VIUS data

    weight_by_tm (boolean): If set to False, just produces distributions of event numbers, rather than weighting by ton-miles

    Returns
    -------
    None

    NOTE: None.
    """

    region_pretty = get_region_pretty(region)

    if set_commodity_title == "default":
        commodity_pretty = get_commodity_pretty(commodity)
        commodity_title = commodity_pretty
    else:
        commodity_title = set_commodity_title

    if set_commodity_save == "default":
        commodity_save = commodity
    else:
        commodity_save = set_commodity_save

    if set_range_title == "default":
        range_pretty = get_range_pretty(truck_range)
        range_title = range_pretty
    else:
        range_title = set_range_title

    if set_range_save == "default":
        range_save = truck_range
    else:
        range_save = set_range_save

    cNoPassenger = (df["PPASSENGERS"].isna()) | (df["PPASSENGERS"] == 0)
    cBaseline = (
        (~df["GREET_CLASS"].isna())
        & (~df["MILES_ANNL"].isna())
        & (~df["WEIGHTEMPTY"].isna())
        & (~df["FUEL"].isna())
        & cNoPassenger
    )
    cRange = True
    cCommodity = True
    cRegion = True
    if not truck_range == "all":
        cRange = (~df[truck_range].isna()) & (df[truck_range] > range_threshold)
    if not commodity == "all":
        cCommodity = (~df[commodity].isna()) & (df[commodity] > commodity_threshold)
    if not region == "US":
        cRegion = (~df["ADM_STATE"].isna()) & (df["ADM_STATE"] == region)

    cSelection = cRange & cRegion & cCommodity & cBaseline

    # Get the annual ton miles for all fuels
    annual_ton_miles_all = get_annual_ton_miles(
        df,
        cSelection=cSelection,
        truck_range=truck_range,
        commodity=commodity,
        fuel="all",
        greet_class="all",
    )

    if weight_by_tm:
        weights_all = annual_ton_miles_all
    else:
        weights_all = np.ones(len(annual_ton_miles_all))

    # Bin the data according to the GREET vehicle class, and calculate the associated statistical uncertainty using root sum of squared weights (see eg. https://www.pp.rhul.ac.uk/~cowan/stat/notes/errors_with_weights.pdf)
    plt.figure(figsize=(10, 7))
    n, bins = np.histogram(
        df[cSelection]["GREET_CLASS"],
        bins=[0.5, 1.5, 2.5, 3.5, 4.5],
        weights=weights_all,
    )
    n_err = np.sqrt(
        np.histogram(
            df[cSelection]["GREET_CLASS"],
            bins=[0.5, 1.5, 2.5, 3.5, 4.5],
            weights=weights_all**2,
        )[0]
    )
    plt.title(
        f"Commodity: {commodity_title}, Region: {region_pretty}\nRange: {range_title}",
        fontsize=20,
    )
    if weight_by_tm:
        plt.ylabel("Commodity flow (ton-miles)", fontsize=20)
    else:
        plt.ylabel("Samples per Class", fontsize=20)

    # Plot the total along with error bars (the bars themselves are invisible since I only want to show the error bars)
    plt.bar(
        InfoObjects.GREET_classes_dict.values(),
        n,
        yerr=n_err,
        width=0.4,
        ecolor="black",
        capsize=5,
        alpha=0,
        zorder=1000,
    )

    # Add in the distribution for each fuel, stacked on top of one another
    bottom = np.zeros(4)
    for i_fuel in [1, 2, 3, 4]:
        cFuel = (df["FUEL"] == i_fuel) & cSelection

        annual_ton_miles_fuel = get_annual_ton_miles(
            df,
            cSelection=cSelection,
            truck_range=truck_range,
            commodity=commodity,
            fuel=i_fuel,
            greet_class="all",
        )

        if weight_by_tm:
            weights_fuel = annual_ton_miles_fuel
        else:
            weights_fuel = np.ones(len(annual_ton_miles_fuel))

        n, bins = np.histogram(
            df[cFuel]["GREET_CLASS"],
            bins=[0.5, 1.5, 2.5, 3.5, 4.5],
            weights=weights_fuel,
        )
        n_err = np.sqrt(
            np.histogram(
                df[cFuel]["GREET_CLASS"],
                bins=[0.5, 1.5, 2.5, 3.5, 4.5],
                weights=weights_fuel**2,
            )[0]
        )
        plt.bar(
            InfoObjects.GREET_classes_dict.values(),
            n,
            width=0.4,
            alpha=1,
            zorder=1,
            label=InfoObjects.fuels_dict[i_fuel],
            bottom=bottom,
        )
        bottom += n
    plt.legend(fontsize=18)

    region_save = region_pretty.replace(" ", "_")
    aggregated_info = ""
    if aggregated:
        aggregated_info = "_aggregated"

    plt.xticks(rotation=15, ha="right")

    plt.tight_layout()

    weight_str = ""
    if not weight_by_tm:
        weight_str = "_unweighted"

    print(
        f"Saving figure to plots/greet_truck_class_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.png"
    )
    plt.savefig(
        f"plots/greet_truck_class_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.png"
    )
    plt.savefig(
        f"plots/greet_truck_class_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.pdf"
    )
    # plt.show()
    plt.close()


def plot_age_hist(
    df,
    commodity="all",
    truck_range="all",
    region="US",
    range_threshold=0,
    commodity_threshold=0,
    set_commodity_title="default",
    set_commodity_save="default",
    set_range_title="default",
    set_range_save="default",
    aggregated=False,
    weight_by_tm=True,
):
    """
    Calculates and plots the distributions of truck age and GREET truck class for different commodities ('commmodity' parameter), trip range windows ('truck_range' parameter), and administrative states ('region' parameter). Samples used to produce the distributions are weighted by the average annual ton-miles reported carrying the given 'commodity' over the given 'truck_range', for the given administrative 'region'.

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    commodity (string): Name of the column of VIUS data containing the percentage of ton-miles carrying the given commodity

    truck_range (string): Name of the column of VIUS data containing the percentage of ton-miles carried over the given trip range

    region (string): Name of the column of VIUS data containing boolean data to indicate the truck's administrative state

    range_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the truck_range is not 'all'

    commodity_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the commodity is not 'all'

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted commodity to be shown in the plot title

    set_commodity_save (string): Allows the user to set the keyword for the plotted commodity to be included in the filenames of the saved plots

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted trip range to be shown in the plot title

    set_range_save (string): Allows the user to set the keyword for the plotted trip range to be included in the filenames of the saved plots

    aggregated (boolean): If set to True, adds an additional string '_aggregated' to the filenames of the saved plots to indicate that aggregation has been done to obtain common commodity and/or trip range definitions between FAF5 and VIUS data

    weight_by_tm (boolean): If set to False, just produces distributions of event numbers, rather than weighting by ton-miles

    Returns
    -------
    None

    NOTE: None.
    """

    region_pretty = get_region_pretty(region)

    if set_commodity_title == "default":
        commodity_pretty = get_commodity_pretty(commodity)
        commodity_title = commodity_pretty
    else:
        commodity_title = set_commodity_title

    if set_commodity_save == "default":
        commodity_save = commodity
    else:
        commodity_save = set_commodity_save

    if set_range_title == "default":
        range_pretty = get_range_pretty(truck_range)
        range_title = range_pretty
    else:
        range_title = set_range_title

    if set_range_save == "default":
        range_save = truck_range
    else:
        range_save = set_range_save

    cNoPassenger = (df["PPASSENGERS"].isna()) | (df["PPASSENGERS"] == 0)
    cBaseline = (
        (~df["WEIGHTAVG"].isna())
        & (~df["MILES_ANNL"].isna())
        & (~df["WEIGHTEMPTY"].isna())
        & (~df["FUEL"].isna())
        & (~df["ACQUIREYEAR"].isna())
        & cNoPassenger
    )
    cCommodity = True
    cRange = True
    cRegion = True
    if not commodity == "all":
        cCommodity = (~df[commodity].isna()) & (df[commodity] > commodity_threshold)
    if not truck_range == "all":
        cRange = (~df[truck_range].isna()) & (df[truck_range] > range_threshold)
    if not region == "US":
        cRegion = (~df["ADM_STATE"].isna()) & (df["ADM_STATE"] == region)

    cSelection = cCommodity & cRange & cRegion & cBaseline

    # Get the annual ton miles for all classes
    annual_ton_miles_all = get_annual_ton_miles(
        df,
        cSelection=cSelection,
        truck_range=truck_range,
        commodity=commodity,
        fuel="all",
        greet_class="all",
    )

    if weight_by_tm:
        weights_all = annual_ton_miles_all
    else:
        weights_all = np.ones(len(annual_ton_miles_all))

    # Bin the data according to the vehicle age, and calculate the associated statistical uncertainty using root sum of squared weights (see eg. https://www.pp.rhul.ac.uk/~cowan/stat/notes/errors_with_weights.pdf)
    plt.figure(figsize=(10, 7))
    n, bins = np.histogram(
        df[cSelection]["ACQUIREYEAR"] - 1, bins=np.arange(18) - 0.5, weights=weights_all
    )
    n_err = np.sqrt(
        np.histogram(
            df[cSelection]["ACQUIREYEAR"] - 1,
            np.arange(18) - 0.5,
            weights=weights_all**2,
        )[0]
    )
    plt.title(
        f"Commodity: {commodity_title}, Region: {region_pretty}\nRange: {range_title}",
        fontsize=20,
    )
    if weight_by_tm:
        plt.ylabel("Commodity flow (ton-miles)", fontsize=20)
    else:
        plt.ylabel("Samples per Age", fontsize=20)
    plt.xlabel("Age (years)", fontsize=20)

    ticklabels = []
    for i in range(16):
        ticklabels.append(str(i))
    ticklabels.append(">15")
    plt.xticks(np.arange(17), ticklabels)

    # Plot the total along with error bars (the bars themselves are invisible since I only want to show the error bars)
    plt.bar(
        range(17),
        n,
        yerr=n_err,
        width=0.4,
        ecolor="black",
        capsize=5,
        alpha=0,
        zorder=1000,
    )

    # Add in the distribution for each fuel, stacked on top of one another
    bottom = np.zeros(17)
    for i_class in range(1, 5):
        cClass = (df["GREET_CLASS"] == i_class) & cSelection
        annual_ton_miles_fuel = get_annual_ton_miles(
            df,
            cSelection=cSelection,
            truck_range=truck_range,
            commodity=commodity,
            fuel="all",
            greet_class=i_class,
        )

        if weight_by_tm:
            weights_fuel = annual_ton_miles_fuel
        else:
            weights_fuel = np.ones(len(annual_ton_miles_fuel))

        n, bins = np.histogram(
            df[cClass]["ACQUIREYEAR"] - 1,
            bins=np.arange(18) - 0.5,
            weights=weights_fuel,
        )
        n_err = np.sqrt(
            np.histogram(
                df[cClass]["ACQUIREYEAR"] - 1,
                bins=np.arange(18) - 0.5,
                weights=weights_fuel**2,
            )[0]
        )
        plt.bar(
            range(17),
            n,
            width=0.4,
            alpha=1,
            zorder=1,
            label=InfoObjects.GREET_classes_dict[i_class],
            bottom=bottom,
        )
        bottom += n

    plt.legend(fontsize=18)

    region_save = region_pretty.replace(" ", "_")
    aggregated_info = ""
    if aggregated:
        aggregated_info = "_aggregated"

    plt.tight_layout()

    weight_str = ""
    if not weight_by_tm:
        weight_str = "_unweighted"

    print(
        f"Saving figure to plots/age_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.png"
    )
    plt.savefig(
        f"plots/age_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.png"
    )
    plt.savefig(
        f"plots/age_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.pdf"
    )
    # plt.show()
    plt.close()


def plot_gvw_hist(
    df,
    commodity="all",
    truck_range="all",
    region="US",
    range_threshold=0,
    commodity_threshold=0,
    set_commodity_title="default",
    set_commodity_save="default",
    set_range_title="default",
    set_range_save="default",
    aggregated=False,
    weight_by_tm=True,
):
    """
    Calculates and plots the distributions of truck age and GREET truck class for different commodities ('commmodity' parameter), trip range windows ('truck_range' parameter), and administrative states ('region' parameter). Samples used to produce the distributions are weighted by the average annual ton-miles reported carrying the given 'commodity' over the given 'truck_range', for the given administrative 'region'.

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    commodity (string): Name of the column of VIUS data containing the percentage of ton-miles carrying the given commodity

    truck_range (string): Name of the column of VIUS data containing the percentage of ton-miles carried over the given trip range

    region (string): Name of the column of VIUS data containing boolean data to indicate the truck's administrative state

    range_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the truck_range is not 'all'

    commodity_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the commodity is not 'all'

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted commodity to be shown in the plot title

    set_commodity_save (string): Allows the user to set the keyword for the plotted commodity to be included in the filenames of the saved plots

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted trip range to be shown in the plot title

    set_range_save (string): Allows the user to set the keyword for the plotted trip range to be included in the filenames of the saved plots

    aggregated (boolean): If set to True, adds an additional string '_aggregated' to the filenames of the saved plots to indicate that aggregation has been done to obtain common commodity and/or trip range definitions between FAF5 and VIUS data

    weight_by_tm (boolean): If set to False, just produces distributions of event numbers, rather than weighting by ton-miles

    Returns
    -------
    None

    NOTE: None.
    """

    region_pretty = get_region_pretty(region)

    if set_commodity_title == "default":
        commodity_pretty = get_commodity_pretty(commodity)
        commodity_title = commodity_pretty
    else:
        commodity_title = set_commodity_title

    if set_commodity_save == "default":
        commodity_save = commodity
    else:
        commodity_save = set_commodity_save

    if set_range_title == "default":
        range_pretty = get_range_pretty(truck_range)
        range_title = range_pretty
    else:
        range_title = set_range_title

    if set_range_save == "default":
        range_save = truck_range
    else:
        range_save = set_range_save

    cNoPassenger = (df["PPASSENGERS"].isna()) | (df["PPASSENGERS"] == 0)
    cBaseline = (
        (~df["WEIGHTAVG"].isna())
        & (~df["MILES_ANNL"].isna())
        & (~df["WEIGHTEMPTY"].isna())
        & (~df["FUEL"].isna())
        & cNoPassenger
    )
    cCommodity = True
    cRange = True
    cRegion = True
    if not commodity == "all":
        cCommodity = (~df[commodity].isna()) & (df[commodity] > commodity_threshold)
    if not truck_range == "all":
        cRange = (~df[truck_range].isna()) & (df[truck_range] > range_threshold)
    if not region == "US":
        cRegion = (~df["ADM_STATE"].isna()) & (df["ADM_STATE"] == region)

    cSelection = cCommodity & cRange & cRegion & cBaseline

    # Get the annual ton miles for all classes
    annual_ton_miles_all = get_annual_ton_miles(
        df,
        cSelection=cSelection,
        truck_range=truck_range,
        commodity=commodity,
        fuel="all",
        greet_class="all",
    )

    if weight_by_tm:
        weights = annual_ton_miles_all
    else:
        weights = np.ones(len(annual_ton_miles_all))

    # Bin the data according to the vehicle age, and calculate the associated statistical uncertainty using root sum of squared weights (see eg. https://www.pp.rhul.ac.uk/~cowan/stat/notes/errors_with_weights.pdf)
    plt.figure(figsize=(10, 7))
    n, bins = np.histogram(df[cSelection]["WEIGHTAVG"], bins=50, weights=weights)
    n_err = np.sqrt(
        np.histogram(df[cSelection]["WEIGHTAVG"], bins=bins, weights=weights**2)[0]
    )
    plt.title(
        f"Commodity: {commodity_title}, Region: {region_pretty}\nRange: {range_title}",
        fontsize=20,
    )
    plt.ylabel("Samples per Bin", fontsize=20)
    plt.xlabel("Gross Vehicle Weight (lb)", fontsize=20)

    #    ticklabels = []
    #    for i in range(16):
    #        ticklabels.append(str(i))
    #    ticklabels.append('>15')
    #    plt.xticks(np.arange(17), ticklabels)

    bin_centers = bins[:-1] + 0.5 * (bins[1] - bins[0])
    bin_width = bins[1] - bins[0]

    # Plot the total along with error bars (the bars themselves are invisible since I only want to show the error bars)
    plt.bar(bin_centers, n, yerr=n_err, ecolor="black", capsize=5, width=bin_width)

    average = np.average(df[cSelection]["WEIGHTAVG"], weights=weights)
    variance = np.average((df[cSelection]["WEIGHTAVG"] - average) ** 2, weights=weights)
    peak_central = bin_centers[n == np.max(n)]
    std = np.sqrt(variance)
    plt.axvline(
        average, label=f"Mean: {int(average)} lb", linewidth=2, color="red", zorder=101
    )
    plt.axvline(
        peak_central,
        label=f"Peak Central Value: {int(peak_central)} lb",
        color="green",
        linewidth=2,
        zorder=102,
    )
    plt.axvspan(
        average - std,
        average + std,
        label=f"StDev: {int(std)} lb",
        alpha=0.3,
        color="red",
        zorder=100,
    )

    region_save = region_pretty.replace(" ", "_")
    aggregated_info = ""
    if aggregated:
        aggregated_info = "_aggregated"

    plt.legend(fontsize=18)
    plt.tight_layout()

    weight_str = ""
    if not weight_by_tm:
        weight_str = "_unweighted"

    print(
        f"Saving figure to plots/gvw_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.png"
    )
    plt.savefig(
        f"plots/gvw_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.png"
    )
    plt.savefig(
        f"plots/gvw_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}.pdf"
    )
    # plt.show()
    plt.close()


def plot_payload_hist(
    df,
    commodity="all",
    truck_range="all",
    region="US",
    range_threshold=0,
    commodity_threshold=0,
    set_commodity_title="default",
    set_commodity_save="default",
    set_range_title="default",
    set_range_save="default",
    aggregated=False,
    greet_class="all",
    weight_by_tm=True,
    plot_vw_class=False,
):
    """
    Calculates and plots the distributions of truck payload for different commodities ('commmodity' parameter), trip range windows ('truck_range' parameter), and administrative states ('region' parameter). Samples used to produce the distributions are weighted by the average annual ton-miles reported carrying the given 'commodity' over the given 'truck_range', for the given administrative 'region'.

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    commodity (string): Name of the column of VIUS data containing the percentage of ton-miles carrying the given commodity

    truck_range (string): Name of the column of VIUS data containing the percentage of ton-miles carried over the given trip range

    region (string): Name of the column of VIUS data containing boolean data to indicate the truck's administrative state

    range_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the truck_range is not 'all'

    commodity_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the commodity is not 'all'

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted commodity to be shown in the plot title

    set_commodity_save (string): Allows the user to set the keyword for the plotted commodity to be included in the filenames of the saved plots

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted trip range to be shown in the plot title

    set_range_save (string): Allows the user to set the keyword for the plotted trip range to be included in the filenames of the saved plots

    aggregated (boolean): If set to True, adds an additional string '_aggregated' to the filenames of the saved plots to indicate that aggregation has been done to obtain common commodity and/or trip range definitions between FAF5 and VIUS data

    weight_by_tm (boolean): If set to False, just produces distributions of event numbers, rather than weighting by ton-miles

    plot_vw_class (boolean): If set to True, plots distributions in a given GREET class range instead within the equivalent unloaded vehicle weight range, as evaluated by the function add_unloaded_vehicle_weight_class()

    Returns
    -------
    None

    NOTE: None.
    """
    region_pretty = get_region_pretty(region)

    if set_commodity_title == "default":
        commodity_pretty = get_commodity_pretty(commodity)
        commodity_title = commodity_pretty
    else:
        commodity_title = set_commodity_title

    if set_commodity_save == "default":
        commodity_save = commodity
    else:
        commodity_save = set_commodity_save

    if set_range_save == "default":
        range_save = truck_range
    else:
        range_save = set_range_save

    # If the user has enabled the plot_vw_class flag, plot distributions in equivalent unloaded vehicle weight classes instead
    class_str = "GREET_CLASS"
    if plot_vw_class:
        class_str = "UNLOADED_WEIGHT_CLASS"

    cNoPassenger = (df["PPASSENGERS"].isna()) | (df["PPASSENGERS"] == 0)
    cBaseline = (
        (~df["WEIGHTAVG"].isna())
        & (~df["MILES_ANNL"].isna())
        & (~df["WEIGHTEMPTY"].isna())
        & (~df["FUEL"].isna())
        & (~df["ACQUIREYEAR"].isna())
        & cNoPassenger
    )
    cCommodity = True
    cRange = True
    cRegion = True
    if not commodity == "all":
        cCommodity = (~df[commodity].isna()) & (df[commodity] > commodity_threshold)
    if not truck_range == "all":
        cRange = (~df[truck_range].isna()) & (df[truck_range] > range_threshold)
    if not region == "US":
        cRegion = (~df["ADM_STATE"].isna()) & (df["ADM_STATE"] == region)

    # Select the given truck class
    cGreetClass = True
    if not greet_class == "all":
        cGreetClass = (~df[class_str].isna()) & (df[class_str] == greet_class)

    cSelection = cCommodity & cRange & cRegion & cBaseline & cGreetClass
    if np.sum(cSelection) == 0:
        print("ERROR No events in selection. Returning without plotting.")
        return

    # Get the annual ton miles for all classes
    annual_ton_miles_all = get_annual_ton_miles(
        df,
        cSelection=cSelection,
        truck_range=truck_range,
        commodity=commodity,
        fuel="all",
        greet_class="all",
    )

    if weight_by_tm:
        weights_all = annual_ton_miles_all
    else:
        weights_all = np.ones(len(annual_ton_miles_all))
    # Bin the data according to the vehicle age, and calculate the associated statistical uncertainty using root sum of squared weights (see eg. https://www.pp.rhul.ac.uk/~cowan/stat/notes/errors_with_weights.pdf)
    payload = (df[cSelection]["WEIGHTAVG"] - df[cSelection]["WEIGHTEMPTY"]) * LB_TO_TONS
    fig = plt.figure(figsize=(10, 7))
    n, bins = np.histogram(payload, weights=weights_all, bins=10)
    n_err = np.sqrt(np.histogram(payload, weights=weights_all**2, bins=10)[0])

    if plot_vw_class:
        class_title = InfoObjects.VW_classes_dict[greet_class]
    else:
        class_title = InfoObjects.GREET_classes_dict[greet_class]

    if plot_vw_class:
        plt.title(
            f"Commodity: {commodity_title}\nUnloaded VW Class: {class_title}",
            fontsize=20,
        )
    else:
        plt.title(
            f"Commodity: {commodity_title}\nGREET Class: {class_title}", fontsize=20
        )
    if weight_by_tm:
        plt.ylabel("Commodity flow (ton-miles)", fontsize=20)
    else:
        plt.ylabel("Samples per Bin", fontsize=20)
    plt.xlabel("Payload (tons)", fontsize=20)

    #    ticklabels = []
    #    for i in range(16):
    #        ticklabels.append(str(i))
    #    ticklabels.append('>15')
    #    plt.xticks(np.arange(17), ticklabels)

    # Plot the total along with error bars (the bars themselves are invisible since I only want to show the error bars)
    plt.bar(
        bins[:-1] + 0.5 * (bins[1] - bins[0]),
        n,
        yerr=n_err,
        width=bins[1] - bins[0],
        ecolor="black",
        capsize=5,
    )

    # Also calculate the mean (+/- stdev) age and report it on the plot
    mean_payload = np.average(payload, weights=weights_all)
    variance_payload = np.average((payload - mean_payload) ** 2, weights=weights_all)
    std_payload = np.sqrt(variance_payload)
    plt.text(
        0.5,
        0.7,
        "mean payload: %.1f±%.1f tons" % (mean_payload, std_payload),
        transform=fig.axes[0].transAxes,
        fontsize=18,
    )
    #    plt.legend()

    region_save = region_pretty.replace(" ", "_")
    aggregated_info = ""
    if aggregated:
        aggregated_info = "_aggregated"

    if greet_class == "all":
        greet_class_str = "all"
    else:
        greet_class_str = (
            (InfoObjects.GREET_classes_dict[greet_class])
            .replace(" ", "_")
            .replace("-", "_")
        )

    plt.tight_layout()

    weight_str = ""
    if not weight_by_tm:
        weight_str = "_unweighted"

    class_info_str = "greet_class"
    if plot_vw_class:
        class_info_str = "unloaded_weight_class"

    print(
        f"Saving figure to plots/payload_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}_{class_info_str}_{greet_class_str}{weight_str}.png"
    )
    plt.savefig(
        f"plots/payload_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}_{class_info_str}_{greet_class_str}{weight_str}.png"
    )
    plt.savefig(
        f"plots/payload_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}_{class_info_str}_{greet_class_str}{weight_str}.pdf"
    )
    # plt.show()
    plt.close()


def get_bin_centroids(data, weights, bins):
    """
    Calculates the centroid of each bin, accounting for event weights

    Parameters
    ----------
    data (numpy.array): data to be binned

    weights (numpy.array): weight of each event in the data

    bins (np.array): bin edges

    Returns
    -------
    centroids (numpy.array): weighted centroid in each bin

    NOTE: None.
    """
    centroids = np.zeros(0)
    for i in range(len(bins) - 1):
        data_in_bin = data[(data >= bins[i]) & (data < bins[i + 1])]
        weights_in_bin = weights[(data >= bins[i]) & (data < bins[i + 1])]

        # If there's no data in the bin, set the centroid to the bin center
        if len(data_in_bin) == 0:
            centroid = 0.5 * (bins[i] + bins[i + 1])
            centroids = np.append(centroids, centroid)

        else:
            centroid = np.average(data_in_bin, weights=weights_in_bin)
            centroids = np.append(centroids, centroid)

    return centroids


def plot_mpg_times_payload_hist(
    df,
    commodity="all",
    truck_range="all",
    region="US",
    range_threshold=0,
    commodity_threshold=0,
    set_commodity_title="default",
    set_commodity_save="default",
    set_range_title="default",
    set_range_save="default",
    aggregated=False,
    weight_by_tm=True,
    binning=10,
    binning_info="",
    density=False,
):
    """
    Calculates and plots the distributions of miles per gallon times payload for different commodities ('commmodity' parameter), trip range windows ('truck_range' parameter), and administrative states ('region' parameter). Samples used to produce the distributions are weighted by the average annual ton-miles reported carrying the given 'commodity' over the given 'truck_range', for the given administrative 'region'.

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    commodity (string): Name of the column of VIUS data containing the percentage of ton-miles carrying the given commodity

    truck_range (string): Name of the column of VIUS data containing the percentage of ton-miles carried over the given trip range

    region (string): Name of the column of VIUS data containing boolean data to indicate the truck's administrative state

    range_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the truck_range is not 'all'

    commodity_threshold (float): Threshold percentage of ton-miles carried over the given range required to include the a truck in the analysis, in cases where the commodity is not 'all'

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted commodity to be shown in the plot title

    set_commodity_save (string): Allows the user to set the keyword for the plotted commodity to be included in the filenames of the saved plots

    set_commodity_title (string): Allows the user to set the human-readable name for the plotted trip range to be shown in the plot title

    set_range_save (string): Allows the user to set the keyword for the plotted trip range to be included in the filenames of the saved plots

    aggregated (boolean): If set to True, adds an additional string '_aggregated' to the filenames of the saved plots to indicate that aggregation has been done to obtain common commodity and/or trip range definitions between FAF5 and VIUS data

    weight_by_tm (boolean): If set to False, just produces distributions of event numbers, rather than weighting by ton-miles

    binning (int or Numpy.array): Either the number of bins in the histogram (if an int), or the bin edges (if an array)

    binning_info (string): Optionally, specify an informational string to include in the filename of the plotted histogram to describe the binning that took place

    density (boolean): Specifies whether or not to normalize the bin heights to represent probability density.

    Returns
    -------
    None

    NOTE: None.
    """
    region_pretty = get_region_pretty(region)

    if set_commodity_title == "default":
        commodity_pretty = get_commodity_pretty(commodity)
        commodity_title = commodity_pretty
    else:
        commodity_title = set_commodity_title

    if set_commodity_save == "default":
        commodity_save = commodity
    else:
        commodity_save = set_commodity_save

    if set_range_save == "default":
        range_save = truck_range
    else:
        range_save = set_range_save

    cNoPassenger = (df["PPASSENGERS"].isna()) | (df["PPASSENGERS"] == 0)
    cBaseline = (
        (df["WEIGHTAVG"] > 8500)
        & (~df["MILES_ANNL"].isna())
        & (~df["WEIGHTEMPTY"].isna())
        & (~df["FUEL"].isna())
        & (~df["ACQUIREYEAR"].isna())
        & cNoPassenger
    )
    cCommodity = True
    cRange = True
    cRegion = True
    if not commodity == "all":
        cCommodity = (~df[commodity].isna()) & (df[commodity] > commodity_threshold)
    if not truck_range == "all":
        cRange = (~df[truck_range].isna()) & (df[truck_range] > range_threshold)
    if not region == "US":
        cRegion = (~df["ADM_STATE"].isna()) & (df["ADM_STATE"] == region)

    cSelection = cCommodity & cRange & cRegion & cBaseline
    if np.sum(cSelection) == 0:
        print("ERROR No events in selection. Returning without plotting.")
        return

    # Get the annual ton miles for all classes
    annual_ton_miles_all = get_annual_ton_miles(
        df,
        cSelection=cSelection,
        truck_range=truck_range,
        commodity=commodity,
        fuel="all",
        greet_class="all",
    )

    if weight_by_tm:
        weights_all = annual_ton_miles_all
    else:
        weights_all = np.ones(len(annual_ton_miles_all))

    # Bin the data according to the vehicle age, and calculate the associated statistical uncertainty using root sum of squared weights (see eg. https://www.pp.rhul.ac.uk/~cowan/stat/notes/errors_with_weights.pdf)]]
    payload = (df[cSelection]["WEIGHTAVG"] - df[cSelection]["WEIGHTEMPTY"]) * LB_TO_TONS
    mpg_times_payload = df[cSelection]["MPG"] * payload

    # Remove any zeros or infs
    weights_all = weights_all[(mpg_times_payload > 0)]  # &(mpg_times_payload < 2)
    mpg_times_payload = mpg_times_payload[
        (mpg_times_payload > 0)
    ]  # &(mpg_times_payload < 2)

    fig = plt.figure(figsize=(10, 7))
    n, bins = np.histogram(mpg_times_payload, weights=weights_all, bins=binning)
    n_err = np.sqrt(
        np.histogram(mpg_times_payload, weights=weights_all**2, bins=binning)[0]
    )

    # If density argument is supplied, calculate the probability density for each bin
    if density:
        bin_widths = binning[:-1] - binning[1:]
        n_density = n / bin_widths
        n_density = n_density / np.sum(n_density)
        n_err_density = n_err * n_density / n
        n_err_density[np.isinf(n_err_density)] = 0

    plt.title(f"Commodity: {commodity_title}, Range: {truck_range}", fontsize=20)
    if weight_by_tm:
        if density:
            plt.ylabel("Probability Density per Bin", fontsize=20)
        else:
            plt.ylabel("Commodity flow (ton-miles)", fontsize=20)
    else:
        plt.ylabel("Samples per Bin", fontsize=20)
    plt.xlabel("Fuel Efficiency $\\times$ Payload (ton-mpg)", fontsize=20)

    # Plot the total along with error bars (the bars themselves are invisible since I only want to show the error bars)
    bin_centers = bins[:-1] + 0.5 * (bins[1:] - bins[:-1])
    centroids = get_bin_centroids(mpg_times_payload, weights_all, binning)
    if density:
        plt.bar(
            bin_centers,
            n_density,
            yerr=n_err_density,
            width=bins[1:] - bins[:-1],
            ecolor="black",
            capsize=5,
        )
    else:
        plt.bar(
            bin_centers,
            n,
            yerr=n_err,
            width=bins[1:] - bins[:-1],
            ecolor="black",
            capsize=5,
        )

    i_centroid = 0
    for centroid in centroids:
        if i_centroid == 0:
            plt.plot(centroid, 0, "o", color="red", label="bin centroids")
        else:
            plt.plot(centroid, 0, "o", color="red")

        i_centroid += 1

    # Also calculate the mean (+/- stdev) and report it on the plot
    mean_mpg_times_payload = np.average(mpg_times_payload, weights=weights_all)
    variance_mpg_times_payload = np.average(
        (mpg_times_payload - mean_mpg_times_payload) ** 2, weights=weights_all
    )
    std_mpg_times_payload = np.sqrt(variance_mpg_times_payload)
    plt.text(
        0.5,
        0.7,
        "mean: %.1f±%.1f ton-mpg" % (mean_mpg_times_payload, std_mpg_times_payload),
        transform=fig.axes[0].transAxes,
        fontsize=18,
    )
    #    plt.legend()

    region_save = region_pretty.replace(" ", "_")
    aggregated_info = ""
    if aggregated:
        aggregated_info = "_aggregated"

    plt.legend(fontsize=18)
    plt.tight_layout()

    weight_str = ""
    if not weight_by_tm:
        weight_str = "_unweighted"

    density_str = ""
    if density:
        density_str = "_density"

    print(
        f"Saving figure to plots/mpg_times_payload_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}{binning_info}{density_str}.png"
    )
    plt.savefig(
        f"plots/mpg_times_payload_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}{binning_info}{density_str}.png"
    )
    plt.savefig(
        f"plots/mpg_times_payload_distribution{aggregated_info}_range_{range_save}_commodity_{commodity_save}_region_{region_save}{weight_str}{binning_info}{density_str}.pdf"
    )
    # plt.show()
    plt.close()


def plot_mpg_scatter(df, x_var="gvw", nBins=30):
    """
    Plots a scatterplot of miles per gallon (mpg) as a function of the given variable, and also plots the running average and standard deviation.

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    x_car (string): String identifier of the variable to plot on the x-axis

    nBins (integer): Number of bins in the x-variable within which to evaluate the running average and standard deviation


    Returns
    -------
    None

    NOTE: None.
    """
    plt.figure(figsize=(10, 7))
    plt.ylabel("Miles per Gallon", fontsize=20)
    cSelection = (
        make_basic_selections(df)
        & (~df["MPG"].isna())
        & (~df["WEIGHTAVG"].isna())
        & (~df["ACQUIREYEAR"].isna())
    )  # & (df['WEIGHTAVG'] > 20000) & (df['WEIGHTAVG'] < 75000) #& (df['WEIGHTAVG'] > 8500)

    # Calculate the point density
    if x_var == "gvw":
        x = df["WEIGHTAVG"][cSelection]
        x_nosel = df["WEIGHTAVG"]
        plt.title("Vehicle weight dependence of mpg for diesel trucks", fontsize=20)
        plt.xlabel("Average Gross Vehicle Weight (lb)", fontsize=20)
        bin_title = "lb"
        min_bin = min(x)
    elif x_var == "payload":
        x = (df["WEIGHTAVG"][cSelection] - df["WEIGHTEMPTY"][cSelection]) * LB_TO_TONS
        x_nosel = (df["WEIGHTAVG"] - df["WEIGHTEMPTY"]) * LB_TO_TONS
        plt.title("Payload dependence of mpg for diesel trucks", fontsize=20)
        plt.xlabel("Average Payload (tons)", fontsize=20)
        bin_title = "ton"
        min_bin = min(x)
        max_bin = max(x)
    elif x_var == "age":
        x = df["ACQUIREYEAR"][cSelection] - 1
        nBins = 16
        x_nosel = df["ACQUIREYEAR"] - 1
        plt.title("Age dependence of mpg for diesel trucks", fontsize=20)
        plt.xlabel("Age (years)", fontsize=20)
        bin_title = "year"
        min_bin = 0
        max_bin = 16

        ticklabels = []
        for i in range(16):
            ticklabels.append(str(i))
        ticklabels.append(">15")
        plt.xticks(np.arange(17), ticklabels)

    mpg = df["MPG"][cSelection]
    # xy = np.vstack([x, mpg])
    # z = gaussian_kde(xy)(xy)

    # plt.scatter(x, y, c=z, s=10)
    plt.plot(x, mpg, "o", markersize=2)

    # Plot the average and standard deviation
    bins = np.linspace(min_bin, max_bin, nBins + 1)
    bin_width = bins[1] - bins[0]
    bin_centers = bins[:-1] + 0.5 * bin_width
    mpg_avs = np.zeros(0)
    mpg_stds = np.zeros(0)

    for i_bin in np.arange(nBins):
        mpg_bin = mpg[(x >= bins[i_bin]) & (x < bins[i_bin + 1])]
        if len(mpg_bin) < 5:
            mpg_avs = np.append(mpg_avs, np.nan)
            mpg_stds = np.append(mpg_stds, np.nan)
            continue
        annual_ton_miles = get_annual_ton_miles(
            df,
            cSelection=cSelection
            & (x_nosel >= bins[i_bin])
            & (x_nosel < bins[i_bin + 1]),
            truck_range="all",
            commodity="all",
            fuel="all",
            greet_class="all",
        )
        mpg_av = np.average(mpg_bin, weights=annual_ton_miles)
        mpg_variance = np.average((mpg_bin - mpg_av) ** 2, weights=annual_ton_miles)
        mpg_std = np.sqrt(mpg_variance)

        mpg_avs = np.append(mpg_avs, mpg_av)
        mpg_stds = np.append(mpg_stds, mpg_std)

    if x_var == "age":
        x_plot = range(16)
    else:
        x_plot = bin_centers

    plt.plot(
        x_plot,
        mpg_avs,
        color="red",
        label=f"Average MPG per {int(bin_width)}-{bin_title} bin\n(weighted by average annual ton-miles)",
        linewidth=2,
    )
    plt.fill_between(
        x_plot,
        mpg_avs + mpg_stds,
        mpg_avs - mpg_stds,
        color="orange",
        alpha=0.5,
        zorder=10,
        label="Standard deviation of the average",
    )
    plt.legend(fontsize=16)

    print(f"Saving figure to plots/mpg_vs_{x_var}.png")
    plt.savefig(f"plots/mpg_vs_{x_var}.png")
    plt.savefig(f"plots/mpg_vs_{x_var}.pdf")


def plot_x_vs_y(df, x, y, x_title, y_title, x_save, y_save):
    """
    Plots a kde density scatterplot of the given quantities

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    x (string): String identifier of the variable to plot on the x-axis

    y (string): String identifier of the variable to plot on the y-axis

    x_title (string): x-axis title

    y_title (string): y-axis title

    x_save (string): string identifier for the x variable to be included in the filename that the plot is saved to

    y_save (string): string identifier for the y variable to be included in the filename that the plot is saved to

    Returns
    -------
    None

    NOTE: None.
    """
    plt.figure(figsize=(10, 7))
    cSelection = make_basic_selections(df) & (~df[x].isna()) & (~df[y].isna())
    plt.xlabel(x_title, fontsize=20)
    plt.ylabel(y_title, fontsize=20)

    xy = np.vstack([df[x][cSelection], df[y][cSelection]])
    z = gaussian_kde(xy)(xy)
    plt.scatter(df[x][cSelection], df[y][cSelection], c=z, s=10)

    # plt.plot(df[x][cSelection], df[y][cSelection], 'o', markersize=2)

    print(f"Saving to plots/{x_save}_vs_{y_save}.png")

    plt.savefig(f"plots/{x_save}_vs_{y_save}.png")
    plt.savefig(f"plots/{x_save}_vs_{y_save}.pdf")


def add_unloaded_vehicle_weight_class(df):
    """
    Adds classes for unloaded vehicle weight, with the weight values used to define each class defined such that the same fraction of events fall into each unloaded vehicle weight class compared with the GREET GVW classes

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    Returns
    -------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data, with the unloaded vehicle weight classes added in

    NOTE: None.
    """
    cBasic = make_basic_selections(df) & (~df["GREET_CLASS"].isna())

    greet_bins = [0, 8500, 19500, 33000, 1e9]
    n, bins = np.histogram(df["WEIGHTAVG"][cBasic], bins=greet_bins)
    event_fractions = n / len(df["WEIGHTAVG"][cBasic])

    #    for i_class in range(1,5):
    #        print(f'GREET class: {InfoObjects.GREET_classes_dict[i_class]}: \nFraction of Events: {event_fractions[4-i_class]*100}%')

    # Get the quantiles
    quantiles = np.zeros(1)
    for i in range(1, 5):
        quantiles = np.append(quantiles, np.sum(event_fractions[0:i]))

    # Fill the unloaded vehicle weight classes sucha that they have the equivalent quantiles as the GREET classes
    from scipy import stats

    bin_edges_equivalent = stats.mstats.mquantiles(df["WEIGHTEMPTY"], quantiles)

    df["UNLOADED_WEIGHT_CLASS"] = df.copy(deep=False)["WEIGHTAVG"]

    df.loc[df["WEIGHTEMPTY"] >= bin_edges_equivalent[3], "UNLOADED_WEIGHT_CLASS"] = (
        get_key_from_value(InfoObjects.GREET_classes_dict, "Heavy GVW")
    )
    df.loc[
        (df["WEIGHTEMPTY"] >= bin_edges_equivalent[2])
        & (df["WEIGHTEMPTY"] < bin_edges_equivalent[3]),
        "UNLOADED_WEIGHT_CLASS",
    ] = get_key_from_value(InfoObjects.GREET_classes_dict, "Medium GVW")
    df.loc[
        (df["WEIGHTEMPTY"] >= bin_edges_equivalent[1])
        & (df["WEIGHTEMPTY"] < bin_edges_equivalent[2]),
        "UNLOADED_WEIGHT_CLASS",
    ] = get_key_from_value(InfoObjects.GREET_classes_dict, "Light GVW")
    df.loc[df["WEIGHTEMPTY"] < bin_edges_equivalent[1], "UNLOADED_WEIGHT_CLASS"] = (
        get_key_from_value(InfoObjects.GREET_classes_dict, "Light-duty")
    )

    return df


def plot_y_vs_trip_range(df, y_str, y_title):
    """
    Plots the given value as a function of trip range, and evaluates the mean and std for each trip range

    Parameters
    ----------
    df (pd.DataFrame): A pandas dataframe containing the VIUS data

    y_str (string): String identifier of the variable to plot on the y-axis

    t_title (string): Title to describe the variable plotted on the y-axis

    Returns
    -------
    None

    NOTE: None.
    """

    plt.figure(figsize=(10, 7))
    plt.xlabel("Trip range (miles)", fontsize=20)
    plt.ylabel(y_title, fontsize=20)
    cBasic = make_basic_selections(df)
    weighted_means = {"range": [], "weighted mean": [], "weighted std": [], "x": []}
    i = 0

    for trip_range in [
        "TRIP0_50",
        "TRIP051_100",
        "TRIP101_200",
        "TRIP201_500",
        "TRIP500MORE",
    ]:
        weighted_means["range"].append(trip_range)
        cSelection = cBasic & (df[trip_range] > 0) & ~(df[y_str].isna())
        weighted_mean = np.average(
            df[y_str][cSelection], weights=df[trip_range][cSelection] / 100.0
        )
        weighted_variance = np.average(
            (df[y_str][cSelection] - weighted_mean) ** 2,
            weights=df[trip_range][cSelection] / 100.0,
        )
        weighted_std = np.sqrt(weighted_variance)
        weighted_means["weighted mean"].append(weighted_mean)
        weighted_means["weighted std"].append(weighted_std)
        weighted_means["x"].append(df[y_str][cSelection])

        if i == 0:
            plt.plot(
                i * (np.ones(len(df[y_str][cSelection]))),
                df[y_str][cSelection],
                "o",
                color="black",
                label="Samples",
                markersize=1,
            )
        else:
            plt.plot(
                i * (np.ones(len(df[y_str][cSelection]))),
                df[y_str][cSelection],
                "o",
                color="black",
                markersize=1,
            )
        i += 1
    plt.plot(
        np.arange(len(weighted_means["range"])),
        weighted_means["weighted mean"],
        "o",
        markersize=10,
        label="Average",
        color="red",
    )
    plt.errorbar(
        np.arange(len(weighted_means["range"])),
        weighted_means["weighted mean"],
        yerr=weighted_means["weighted std"],
        fmt="o",
        color="red",
        ecolor="blue",
        linewidth=3,
        capsize=5,
        label="Standard Deviation",
        zorder=100,
    )
    plt.xticks(
        np.arange(len(weighted_means["range"])),
        ["0-50", "51-100", "101-200", "201-500", ">500"],
    )
    plt.legend(fontsize=16)
    print(f"Saving figure to plots/{y_str}_vs_TripRange.png")
    plt.savefig(f"plots/{y_str}_vs_TripRange.png")


######################################### Plot some distributions #########################################
# Read in the VIUS data (from https://rosap.ntl.bts.gov/view/dot/42632) as a dataframe
df_vius = pd.read_csv(f"{top_dir}/data/VIUS_2002/bts_vius_2002_data_items.csv")
df_vius = add_GREET_class(df_vius)
df_vius = add_payload(df_vius)
df_vius = divide_mpg_by_10(df_vius)
df_vius = add_unloaded_vehicle_weight_class(df_vius)

df_agg = make_aggregated_df(df_vius)

df_agg_coarse_range = make_aggregated_df(
    df_vius, range_map=InfoObjects.FAF5_VIUS_range_map_coarse
)

"""

# Basic sanity checks to make sure sum of aggregated column is equal to combined sum of its constituent columns
df_agg_wood_sum = np.sum(df_agg['Wood products'])
df_vius_wood_sum = np.sum(df_vius['PPAPER']) + np.sum(df_vius['PNEWSPRINT']) + np.sum(df_vius['PPRINTPROD'])
print(f'Sum of wood product percentages from df_agg: {df_agg_wood_sum}\nSum of wood product percentages from df_vius: {df_vius_wood_sum}')

df_agg_coarse_below_250 = np.sum(df_agg_coarse_range['Below 250 miles'])
df_agg_below_250 = np.sum(df_agg['Below 100 miles']) + np.sum(df_agg['100 to 250 miles'])
df_vius_below_250 = np.sum(df_vius['TRIP0_50']) + np.sum(df_vius['TRIP051_100']) + np.sum(df_vius['TRIP101_200'])
print(f'Sum of trip range percentages below 250 miles from df_agg_coarse_range: {df_agg_coarse_below_250}\nSum of trip range percentages below 250 miles from df_agg: {df_agg_below_250}\nSum of trip range percentages below 250 miles from df_vius: {df_vius_below_250}')

####################### Informational printouts #######################
# Print out the total number of samples of each commodity, and the total number of commodities
print_all_commodities(df_vius)

# Print out the number of samples for each state in the VIUS, as well as the total number of samples
print_all_states(df_vius)

# Print out the number of aggregated commodities
n_aggregated_commodities = len(InfoObjects.FAF5_VIUS_commodity_map)
print(f'Number of aggregated commodities: {n_aggregated_commodities}')

#######################################################################


################### GREET truck class distributions ###################

# ------- Without aggregated commodities/ranges -------#

# Make a distribution of GREET truck class for all regions, commodities, and vehicle range
plot_greet_class_hist(df_vius, commodity='all', truck_range='all', region='US', range_threshold=0, commodity_threshold=0)
plot_greet_class_hist(df_vius, commodity='all', truck_range='all', region='US', range_threshold=0, commodity_threshold=0, weight_by_tm = False)

# Make distributions of GREET truck class and fuel types for each commodity
for commodity in InfoObjects.pretty_commodities_dict:
    plot_greet_class_hist(df_vius, commodity=commodity, truck_range='all', region='US', range_threshold=0, commodity_threshold=0)

# Make distributions of GREET truck class and fuel types for each state
for state in InfoObjects.states_dict:
    plot_greet_class_hist(df_vius, commodity='all', truck_range='all', region=state, range_threshold=0, commodity_threshold=0)

# Make distributions of GREET truck class and fuel types for each state and commodity
for state in InfoObjects.states_dict:
    for commodity in InfoObjects.pretty_commodities_dict:
        plot_greet_class_hist(df_vius, region=state, commodity=commodity)

# Make distributions of GREET truck class with respect to both commodity and range
for truck_range in InfoObjects.pretty_range_dict:
    for commodity in InfoObjects.pretty_commodities_dict:
        plot_greet_class_hist(df_vius, commodity=commodity, truck_range=truck_range, region='US', range_threshold=0, commodity_threshold=0)

# Make distributions of GREET truck class and fuel types for each vehicle range
for truck_range in InfoObjects.pretty_range_dict:
    plot_greet_class_hist(df_vius, commodity='all', truck_range=truck_range, region='US', range_threshold=0, commodity_threshold=0)

# -----------------------------------------------------#

# -------- With aggregated commodities/ranges ---------#

# Make distributions of GREET truck class and fuel types for each aggregated commodity
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    plot_greet_class_hist(df_agg, commodity=commodity, truck_range='all', region='US', range_threshold=0, commodity_threshold=0, set_commodity_title = commodity, set_commodity_save = InfoObjects.FAF5_VIUS_commodity_map[commodity]['short name'], aggregated=True)

# Make distributions of GREET truck class and fuel types for each state and aggregated commodity
for state in InfoObjects.states_dict:
    for commodity in InfoObjects.FAF5_VIUS_commodity_map:
        plot_greet_class_hist(df_agg, commodity=commodity, truck_range='all', region=state, range_threshold=0, commodity_threshold=0, set_commodity_title = commodity, set_commodity_save = InfoObjects.FAF5_VIUS_commodity_map[commodity]['short name'], aggregated=True)

# Make distributions of GREET truck class with respect to both aggregated commodity and range
for truck_range in InfoObjects.FAF5_VIUS_range_map:
    for commodity in InfoObjects.FAF5_VIUS_commodity_map:
        plot_greet_class_hist(df_agg, commodity=commodity, truck_range=truck_range, region='US', range_threshold=0, commodity_threshold=0, set_commodity_title = commodity, set_commodity_save = InfoObjects.FAF5_VIUS_commodity_map[commodity]['short name'], set_range_title = truck_range, set_range_save = InfoObjects.FAF5_VIUS_range_map[truck_range]['short name'], aggregated=True)

# Make distributions of GREET truck class with respect to both aggregated commodity and coarsely-aggregated range
for truck_range in InfoObjects.FAF5_VIUS_range_map_coarse:
    for commodity in InfoObjects.FAF5_VIUS_commodity_map:
        plot_greet_class_hist(df_agg_coarse_range, commodity=commodity, truck_range=truck_range, region='US', range_threshold=0, commodity_threshold=0, set_commodity_title = commodity, set_commodity_save = InfoObjects.FAF5_VIUS_commodity_map[commodity]['short name'], set_range_title = truck_range, set_range_save = InfoObjects.FAF5_VIUS_range_map_coarse[truck_range]['short name'], aggregated=True)

# Make distributions of GREET truck class and fuel types for each aggregated vehicle range
for truck_range in InfoObjects.FAF5_VIUS_range_map:
    plot_greet_class_hist(df_agg, commodity='all', truck_range=truck_range, region='US', range_threshold=0, commodity_threshold=0, set_range_title = truck_range, set_range_save = InfoObjects.FAF5_VIUS_range_map[truck_range]['short name'], aggregated=True)

# -----------------------------------------------------#

#######################################################################

################### Truck age distributions ###########################

# ------- Without aggregated commodities/ranges -------#

# Make distributions of truck age for all regions, commodities, and vehicle range
plot_age_hist(df_vius, region='US', commodity='all', truck_range='all', range_threshold=0, commodity_threshold=0)
plot_age_hist(df_vius, region='US', commodity='all', truck_range='all', range_threshold=0, commodity_threshold=0, weight_by_tm=False)

# Make distributions of truck age and GREET class for each commodity
for commodity in InfoObjects.pretty_commodities_dict:
    plot_age_hist(df_vius, region='US', commodity=commodity, truck_range='all', range_threshold=0, commodity_threshold=0)

# Make distributions of truck age and GREET class for each range
for truck_range in InfoObjects.pretty_range_dict:
    plot_age_hist(df_vius, region='US', commodity='all', truck_range=truck_range, range_threshold=0, commodity_threshold=0)

# -----------------------------------------------------#

# -------- With aggregated commodities/ranges ---------#

# Make distributions of truck age and GREET class for each aggregated commodity
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    plot_age_hist(df_agg, region='US', commodity=commodity, truck_range='all', range_threshold=0, commodity_threshold=0, set_commodity_title = commodity, set_commodity_save = InfoObjects.FAF5_VIUS_commodity_map[commodity]['short name'], aggregated=True)

# Make distributions of truck age and GREET class for each aggregated range
for truck_range in InfoObjects.FAF5_VIUS_range_map:
    plot_age_hist(df_agg, commodity='all', truck_range=truck_range, region='US', range_threshold=0, commodity_threshold=0, set_range_title = truck_range, set_range_save = InfoObjects.FAF5_VIUS_range_map[truck_range]['short name'], aggregated=True)

# Make distributions of truck age and GREET class for each coarsely aggregated range
for truck_range in InfoObjects.FAF5_VIUS_range_map_coarse:
    plot_age_hist(df_agg_coarse_range, commodity='all', truck_range=truck_range, region='US', range_threshold=0, commodity_threshold=0, set_range_title = truck_range, set_range_save = InfoObjects.FAF5_VIUS_range_map_coarse[truck_range]['short name'], aggregated=True)

# -----------------------------------------------------#

#######################################################################
"""
################## Truck payload distributions ########################

# ------- Without aggregated commodities/ranges -------#
# Make payload distributions of truck age for all regions, commodities, and vehicle range
plot_payload_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
)
plot_payload_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
    weight_by_tm=False,
)

# Make distributions of payload for each GREET class
for greet_class in range(1, 5):
    plot_payload_hist(
        df_agg,
        region="US",
        commodity="all",
        truck_range="all",
        range_threshold=0,
        commodity_threshold=0,
        greet_class=greet_class,
    )

for vw_class in range(1, 5):
    plot_payload_hist(
        df_agg,
        region="US",
        commodity="all",
        truck_range="all",
        range_threshold=0,
        commodity_threshold=0,
        greet_class=vw_class,
        plot_vw_class=True,
    )

# -----------------------------------------------------#

# ------- Without aggregated commodities/ranges -------#
# Make distributions of payload for each aggregated commodity
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    plot_payload_hist(
        df_agg,
        region="US",
        commodity=commodity,
        truck_range="all",
        range_threshold=0,
        commodity_threshold=0,
        set_commodity_title=commodity,
        set_commodity_save=InfoObjects.FAF5_VIUS_commodity_map[commodity]["short name"],
        aggregated=True,
    )

# Make distributions of payload for each aggregated commodity and truck class
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    for greet_class in range(1, 5):
        plot_payload_hist(
            df_agg,
            region="US",
            commodity=commodity,
            truck_range="all",
            range_threshold=0,
            commodity_threshold=0,
            set_commodity_title=commodity,
            set_commodity_save=InfoObjects.FAF5_VIUS_commodity_map[commodity][
                "short name"
            ],
            aggregated=True,
            greet_class=greet_class,
        )

# -----------------------------------------------------#


#######################################################################

################## MPG over payload distributions ########################

# Make payload distributions of truck age for all regions, commodities, and vehicle range
plot_mpg_times_payload_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
    binning=np.linspace(0, 500, 10),
    binning_info="",
    density=False,
)
plot_mpg_times_payload_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
    binning=np.asarray([0, 50, 100, 125, 150, 200, 600]),
    binning_info="nonequi",
    density=False,
)
plot_mpg_times_payload_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
    binning=np.asarray([0, 50, 100, 125, 150, 200, 600]),
    binning_info="nonequi",
    density=True,
)
plot_mpg_times_payload_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
    weight_by_tm=False,
)

# For each commodity
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    plot_mpg_times_payload_hist(
        df_agg,
        region="US",
        commodity=commodity,
        truck_range="all",
        range_threshold=0,
        commodity_threshold=0,
        set_commodity_title=commodity,
        set_commodity_save=InfoObjects.FAF5_VIUS_commodity_map[commodity]["short name"],
        binning=np.asarray([0, 50, 100, 125, 150, 200, 600]),
        density=True,
    )

# For each range
for truck_range in InfoObjects.FAF5_VIUS_range_map:
    plot_mpg_times_payload_hist(
        df_agg,
        region="US",
        commodity="all",
        truck_range=truck_range,
        range_threshold=0,
        commodity_threshold=0,
        set_range_title=truck_range,
        set_range_save=InfoObjects.FAF5_VIUS_range_map[truck_range]["short name"],
        binning=np.asarray([0, 50, 100, 125, 150, 200, 600]),
        density=True,
    )

# For each coarsely-aggregated range
for truck_range in InfoObjects.FAF5_VIUS_range_map_coarse:
    plot_mpg_times_payload_hist(
        df_agg_coarse_range,
        region="US",
        commodity="all",
        truck_range=truck_range,
        range_threshold=0,
        commodity_threshold=0,
        set_range_title=truck_range,
        set_range_save=InfoObjects.FAF5_VIUS_range_map_coarse[truck_range][
            "short name"
        ],
        binning=np.asarray([0, 50, 100, 125, 150, 200, 600]),
        density=True,
    )

# Make distributions of payload for each aggregated commodity and range
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    for truck_range in InfoObjects.FAF5_VIUS_range_map_coarse:
        plot_mpg_times_payload_hist(
            df_agg_coarse_range,
            region="US",
            commodity=commodity,
            truck_range=truck_range,
            range_threshold=0,
            commodity_threshold=0,
            set_commodity_title=commodity,
            set_commodity_save=InfoObjects.FAF5_VIUS_commodity_map[commodity][
                "short name"
            ],
            set_range_title=truck_range,
            set_range_save=InfoObjects.FAF5_VIUS_range_map_coarse[truck_range][
                "short name"
            ],
            binning=np.asarray([0, 50, 100, 125, 150, 200, 600]),
            density=True,
        )

# -----------------------------------------------------#


#######################################################################

################## Gross Vehicle Weight distributions ########################

# ------- Without aggregated commodities/ranges -------#
# Make payload distributions of truck age for all regions, commodities, and vehicle range
plot_gvw_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
)
plot_gvw_hist(
    df_vius,
    region="US",
    commodity="all",
    truck_range="all",
    range_threshold=0,
    commodity_threshold=0,
    weight_by_tm=False,
)
# -----------------------------------------------------#

# ------- Without aggregated commodities/ranges -------#
# Make distributions of payload for each aggregated commodity
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    plot_payload_hist(
        df_agg,
        region="US",
        commodity=commodity,
        truck_range="all",
        range_threshold=0,
        commodity_threshold=0,
        set_commodity_title=commodity,
        set_commodity_save=InfoObjects.FAF5_VIUS_commodity_map[commodity]["short name"],
        aggregated=True,
    )

# Make distributions of payload for each aggregated commodity and truck class
for commodity in InfoObjects.FAF5_VIUS_commodity_map:
    for greet_class in range(1, 5):
        plot_payload_hist(
            df_agg,
            region="US",
            commodity=commodity,
            truck_range="all",
            range_threshold=0,
            commodity_threshold=0,
            set_commodity_title=commodity,
            set_commodity_save=InfoObjects.FAF5_VIUS_commodity_map[commodity][
                "short name"
            ],
            aggregated=True,
            greet_class=greet_class,
        )

# -----------------------------------------------------#


#######################################################################

###########################################################################################################


######################################### Plot some scatter plots #########################################
# Fuel efficiency (mpg) vs. gross vehicle weight
plot_mpg_scatter(df_agg, x_var="gvw")

# Fuel efficiency (mpg) vs. payload
plot_mpg_scatter(df_agg, x_var="payload")

# Fuel efficiency (mpg) vs. payload
plot_mpg_scatter(df_agg, x_var="age")

# Payload vs. annual miles driven
plot_x_vs_y(
    df_agg,
    x="MILES_ANNL",
    y="PAYLOADAVG",
    x_title="Annual distance driven (miles)",
    y_title="Average payload",
    x_save="MILES_ANNL",
    y_save="PAYLOADAVG",
)

# Payload vs. average loaded (WEIGHTAVG) and unloaded (WEIGHTEMPTY) vehicle weight
plot_x_vs_y(
    df_agg,
    x="WEIGHTAVG",
    y="PAYLOADAVG",
    x_title="Average gross vehicle weight (lb)",
    y_title="Average payload (tons)",
    x_save="WEIGHTAVG",
    y_save="PAYLOADAVG",
)
plot_x_vs_y(
    df_agg,
    x="WEIGHTEMPTY",
    y="PAYLOADAVG",
    x_title="Average unloaded vehicle weight (lb)",
    y_title="Average payload (tons)",
    x_save="WEIGHTEMPTY",
    y_save="PAYLOADAVG",
)

# Payload and fuel efficiency vs. trip range
plot_y_vs_trip_range(df_agg, y_str="PAYLOADAVG", y_title="Payload (tons)")
plot_y_vs_trip_range(df_agg, y_str="MPG", y_title="Fuel Efficiency (mpg)")

###########################################################################################################
