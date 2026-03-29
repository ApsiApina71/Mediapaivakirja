from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from werkzeug.security import check_password_hash, generate_password_hash
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "salaisuus")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///database.db")
db = SQLAlchemy(app)

@app.route("/")
def index():
    result = db.session.execute(text("SELECT id, title FROM works"))
    works = result.fetchall()
    return render_template("index.html", works=works)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    username = request.form["username"]
    password = request.form["password"]
    hash_val = generate_password_hash(password)
    sql = "INSERT INTO users (username, password) VALUES (:username, :password)"
    db.session.execute(text(sql), {"username": username, "password": hash_val})
    db.session.commit()
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    username = request.form["username"]
    password = request.form["password"]
    sql = "SELECT id, password FROM users WHERE username = :username"
    result = db.session.execute(text(sql), {"username": username})
    user = result.fetchone()
    if user and check_password_hash(user.password, password):
        session["user_id"] = user.id
        return redirect("/")
    return redirect("/login")

@app.route("/logout")
def logout():
    del session["user_id"]
    return redirect("/")

@app.route("/new", methods=["GET", "POST"])
def new():
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "GET":
        result = db.session.execute(text("SELECT id, name FROM categories"))
        categories = result.fetchall()
        return render_template("new.html", categories=categories)
    
    title = request.form["title"]
    description = request.form["description"]
    category_ids = request.form.getlist("categories")
    user_id = session["user_id"]

    sql = "INSERT INTO works (title, description, user_id) VALUES (:title, :description, :user_id) RETURNING id"
    result = db.session.execute(text(sql), {"title": title, "description": description, "user_id": user_id})
    work_id = result.fetchone()[0]

    for cat_id in category_ids:
        sql_cat = "INSERT INTO work_categories (work_id, category_id) VALUES (:work_id, :cat_id)"
        db.session.execute(text(sql_cat), {"work_id": work_id, "cat_id": cat_id})

    db.session.commit()
    return redirect("/")

@app.route("/work/<int:id>")
def work(id):
    sql_work_details = "SELECT AVG(rating) as average_rating, COUNT(id) as review_count FROM reviews WHERE work_id = :work_id"
    result = db.session.execute(text(sql_work_details), {"work_id": id})
    stats = result.fetchone()
    return render_template("work.html", id=id, stats=stats)

@app.route("/search")
def search():
    query = request.args.get("query")
    query_string = "%" + query + "%"
    sql_search = "SELECT id, title FROM works WHERE title ILIKE :query OR description ILIKE :query"
    result = db.session.execute(text(sql_search), {"query": query_string})
    search_results = result.fetchall()
    return render_template("search.html", works=search_results)

@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    sql_user_stats = "SELECT COUNT(*) FROM reviews WHERE user_id = :user_id"
    result_stats = db.session.execute(text(sql_user_stats), {"user_id": user_id})
    review_count = result_stats.fetchone()[0]

    sql_user_works = "SELECT id, title FROM works WHERE user_id = :user_id"
    result_works = db.session.execute(text(sql_user_works), {"user_id": user_id})
    works = result_works.fetchall()
    return render_template("profile.html", review_count=review_count, works=works)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/login")
    if request.method == "GET":
        sql = "SELECT id, title, description FROM works WHERE id = :id AND user_id = :user_id"
        result = db.session.execute(text(sql), {"id": id, "user_id": session["user_id"]})
        work = result.fetchone()
        if not work:
            return redirect("/")
        return render_template("edit.html", work=work)
    
    title = request.form["title"]
    description = request.form["description"]
    sql = "UPDATE works SET title = :title, description = :description WHERE id = :id AND user_id = :user_id"
    db.session.execute(text(sql), {"title": title, "description": description, "id": id, "user_id": session["user_id"]})
    db.session.commit()
    return redirect(f"/work/{id}")

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    if "user_id" not in session:
        return redirect("/login")
    sql = "DELETE FROM works WHERE id = :id AND user_id = :user_id"
    db.session.execute(text(sql), {"id": id, "user_id": session["user_id"]})
    db.session.commit()
    return redirect("/")
