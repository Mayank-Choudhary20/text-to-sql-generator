from flask import Flask, render_template, request
from texttosql import text_to_sql
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    sql_query = ""
    user_text = ""
    if request.method == "POST":
        user_text = request.form["text"]
        sql_query = text_to_sql(user_text)
    return render_template("index.html", sql=sql_query, text=user_text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
