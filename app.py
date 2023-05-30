from flask import Flask, render_template, request
from optimizer import summarize, filter, get_categories, optimize
import pandas as pd
from pulp import *

app = Flask(__name__)
df = pd.read_csv("U.csv")


@app.route("/")
def index():
    return render_template(
        "index.html",
        categories=get_categories(df),
        ratings=get_categories(df, ["RATING"])["RATING"],
    )


@app.route("/result", methods=["POST"])
def result():
    result = request.form.to_dict(flat=False)
    # print(result)
    filtered = filter(
        df,
        classifications={
            1: result["CLASS_1"][0],
            2: result["CLASS_2"][0],
            3: result["CLASS_3"][0],
            4: result["CLASS_4"][0],
        },
        rating=result["Rating"][0],
        dur_cell_min=int(result["EFFDUR Max"][0]),
        dur_cell_max=int(result["EFFDUR Min"][0]),
    )
    summary = summarize(
        df,
        classifications={
            1: result["CLASS_1"][0],
            2: result["CLASS_2"][0],
            3: result["CLASS_3"][0],
            4: result["CLASS_4"][0],
        },
        rating=result["Rating"][0],
        dur_cell_min=float(result["EFFDUR Max"][0]),
        dur_cell_max=float(result["EFFDUR Min"][0]),
    )
    return render_template(
        "summary_result.html",
        categories=get_categories(df),
        ratings=get_categories(df, ["RATING"])["RATING"],
        ytm=summary["YTM"],
        oas=summary["OAS"],
        mv=summary["mv"],
    )


@app.route("/optimizer")
def optimizer():
    return render_template("optimizer.html")


@app.route("/optimizer_result", methods=["POST"])
def optimizer_result():
    result = request.form.to_dict(flat=False)
    print(result)
    optimized = optimize(
        df,
        str(result["Metric"][0]),
        pd.Timestamp("2023-03-31"),
        sec_weight=float(result["Sector Max"][0]),
        max_indiv_weight=float(result["Weight Max"][0]),
        delta=int(result["EFFDUR Max"][0]),
    )

    portfo = {v.name: v.varValue for v in optimized.variables() if v.varValue > 0}
    return render_template("optimizer_results.html", portfolio=portfo)


if __name__ == "__main__":
    app.run(debug=True)
