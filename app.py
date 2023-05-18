from flask import Flask, render_template, request
from optimizer import summarize, filter, get_categories
import pandas as pd


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
        dur_cell_min=int(result["EFFDUR Max"][0]),
        dur_cell_max=int(result["EFFDUR Min"][0]),
    )
    return render_template(
        "summary_result.html", ytm=summary["YTM"], oas=summary["OAS"], mv=summary["mv"]
    )


@app.route("/optimizer")
def optimizer():
    return render_template("optimizer.html")


if __name__ == "__main__":
    app.run(debug=True)
