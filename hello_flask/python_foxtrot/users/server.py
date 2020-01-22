from flask import Flask, render_template, request, redirect
from mysqlconnection import connectToMySQL
app = Flask(__name__)

@app.route("/")
def landing():
    return render_template("index.html")

@app.route("/create_user", methods=['POST'])
def on_user_create():
    print(request.form)

    mysql = connectToMySQL("users")

    query = "INSERT into users(first_name, last_name, email, created_at, updated_at) VALUES (%(fn)s, %(ln)s, %(em)s, NOW(), NOW());"

    data = {
        "fn": request.form['fn'],
        "ln": request.form['ln'],
        "em": request.form['em'],
    }

    mysql.query_db(query, data)
    return redirect("/user")

@app.route("/users")
def all_users():   
    mysql = connectToMySQL("users")
    query = "SELECT * FROM users"
    all_users = mysql.query_db(query)
    """
    [] - no users
    [{}..{}]  - 1 -> k
    """

    return render_template("table.html", all_users = all_users)

@app.route("/user/show/<user_id>")
def on_show(user_id):
    mysql = connectToMySQL("users")
    query = "SELECT * FROM users WHERE id = %(u_id)s;"
    data = {
        "u_id": user_id
    }
    user_data = mysql.query_db(query,data)
    if user_data:
        user = user_data[0]
        return render_template("user.html", user = user)
    else: 
        return redirect("/")

@app.route("/user/edit/<user_id>")
def edit(user_id):
    mysql = connectToMySQL("users")
    query = "SELECT * FROM users WHERE id = %(u_id)s;"
    data = {
        "u_id": user_id
    }
    user_data = mysql.query_db(query,data)
    if user_data:
        user = user_data[0]
        return render_template("edit.html", user = user)
    else: 
        return redirect("/")

@app.route("/user/on_edit/<user_id>", methods=['POST'])
def on_edit(user_id):
    mysql = connectToMySQL("users")
    query = "UPDATE users SET first_name = %(fn)s, last_name = %(ln)s, email=%(em)s, updated_at = NOW() WHERE id = %(u_id)s;"
    data = {
        'fn': request.form['fn'],
        'ln': request.form['ln'],
        'em': request.form['em'],
        'u_id': user_id
    }
    mysql.query_db(query,data)
    return redirect(f"/user/show/{user_id}")

@app.route("/user/delete/<user_id>")
def on_delete(user_id):
    mysql = connectToMySQL("users")
    query = "DELETE from users WHERE id = %(u_id)s;"
    data = {
        'u_id': user_id
    }
    mysql.query_db(query,data)
    return redirect("/user")

if __name__ == "__main__":
    app.run(debug=True)