from flask import Flask, render_template, request
from texttosql import text_to_sql
  # import your function

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
    app.run(debug=True)
