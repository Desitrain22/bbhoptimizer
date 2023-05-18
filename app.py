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
    print(result)
    filter(df, )
    print(result)
#    return index()


if __name__ == "__main__":
    app.run(debug=True)
