import pandas as pd
from pulp import *


def optimize(
    u: pd.DataFrame,
    target: str = "OAS",
    date: pd.Timestamp = pd.Timestamp("2023-03-31"),
    sec_weight: float = 0.05,
    max_indiv_weight: float = 0.02,
    delta: int = 3,
):
    # Initialize the Problem
    lp = LpProblem("bond-portfo-optimizer", LpMaximize)
    u = generate_class_weights(u)

    # Per Jorge, the portfolio is to be evaluated for only 1 of the two effective dates
    # Should this not be the case, we'd need to comment line 19
    u = u[u["EFFDATE"].apply(pd.Timestamp) == date]

    # This seems unnecessary given our indexed dataframe; however, we need to ensure no negative values
    # are recorded for a bond; that is, avoid any optimal solution which would involve taking a short
    # position. This is a notable danger, as a solution with short positions exist with negative
    # values to 'limit exposure' to certain sectors (i.e reduce net weight in Industrials under Class 2)
    bond_index = LpVariable.dicts(
        "Bond_ID",
        list(u["SECURITY_ALIAS"]),
        lowBound=0,
        upBound=max_indiv_weight,
        cat="Continuous",
    )

    # objective function declaration
    obj = dict(zip(u["SECURITY_ALIAS"], u[target]))
    lp += lpSum([obj[b] * bond_index[b] for b in bond_index.keys()])

    # restrict our weights to 100% total
    lp += (
        lpSum([1 * bond_index[b] for b in bond_index.keys()]) <= 1,
        "Maximum total weight",
    )

    # Add restrictions for the 3 categories under class 2
    for cat in u.columns[-3:]:
        category = dict(zip(u["SECURITY_ALIAS"], u[cat]))

        lp += (
            lpSum([category[b] * bond_index[b] for b in bond_index.keys()])
            <= sec_weight
        )

    total_dur = u["EFFDUR"].sum()
    eff_dur = dict(zip(u["SECURITY_ALIAS"], u["EFFDUR"].astype(float)))
    lp += lpSum([eff_dur[b] * bond_index[b] for b in bond_index.keys()]) <= (
        total_dur + delta
    )
    lp += lpSum([eff_dur[b] * bond_index[b] for b in bond_index.keys()]) >= (
        total_dur - delta
    )

    lp.writeLP("test.lp")
    lp.solve()
    return lp


def get_categories(
    df: pd.DataFrame, columns: list[str] = ["CLASS_" + str(x) for x in range(1, 5)]
):
    """Given a dataframe and list of columns, returns a dictionary with the given columns as keys and the unique
    elements of the columns (as a list) as the value. This is primarily to gather an iterable collection to be used
    in generating a drop down selection for the user given any universe.

    :param df: an unindexed dataframe of the bond universe U
    :param columns: a list of strings, where each string corresponds to a column of df

    :return: a dictionary of column names from the columns parameters, where values are arrays of unique elements
    """
    result = {}
    for cat in columns:
        result[cat] = list(df[cat].unique())
    return result


def filter(
    df: pd.DataFrame,
    classifications: dict,
    rating: str,
    dur_cell_min: int,
    dur_cell_max: int,
):
    """Given a dataframe, adictionary of classification, rating, and dur_cell, returns a universe filtered by the
    constraints derived from the parameters. That is, a universe such that each bond fills each parameters given

    :param df: an unindexed dataframe of the bond universe U
    :param dict classification: a dictionary with integer keys corresponding to each classification field, and
    string values of the classifcation
    :param str rating: a bond rating, ranging from BBB to AAA
    :param int dur_cell_min: Floor EFFDUR (years)
    :param int dur_cell_max: Ceiling EFFDUR (years)

    :return: a filtered dataframe"""

    # filters = [df["CLASS_"+str(x)] == classifications[x] for x in classifications.keys()].append(df["RATING"] == rating)
    # for filter in filters:
    #    df = df[filter]"""     # Scaleable, but slow compared to brute force filter

    df = df[
        (df["CLASS_1"] == classifications[1])
        & (df["CLASS_2"] == classifications[2])
        & (df["CLASS_3"] == classifications[3])
        & (df["CLASS_4"] == classifications[4])
        & (df["RATING"] == rating)
        & (df["EFFDUR"] > dur_cell_min)
        & (df["EFFDUR"] < dur_cell_max)
    ]
    return df


def summarize(
    df: pd.DataFrame,
    classifications: list[str],
    rating: str,
    dur_cell_min,
    dur_cell_max,
):
    df = filter(df, classifications, rating, dur_cell_min, dur_cell_max)
    result = {"OAS": {}, "YTM": {}}
    result["mv"] = df["MV"].sum()
    for metric in ["OAS", "YTM"]:
        result[metric]["min"] = df[metric].min()
        result[metric]["max"] = df[metric].max()
        result[metric]["mean"] = df[metric].mean()
        result[metric]["median"] = df[metric].median()
    return result


def generate_class_weights(df: pd.DataFrame, class_column: str = "CLASS_2"):
    """Given a bond universe dataframe and column name, generates columns identifying whether or not a bond falls
    within a classification type for each unique classifier within the column given (by default, class 2).
    Appended columns utilize integer formating, with 1 representing a boolean true, and 0 a boolean false

    :param
    """
    for field in df[class_column].unique():
        df[field] = (df[class_column] == field).apply(lambda x: 1 if x else 0)
    return df
