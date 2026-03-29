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



sql_work_details = "SELECT AVG(rating) as average_rating, COUNT(id) as review_count FROM reviews WHERE work_id = :work_id"
result = db.session.execute(text(sql_work_details), {"work_id": work_id})
stats = result.fetchone()



sql_user_stats = "SELECT COUNT(*) FROM reviews WHERE user_id = :user_id"
result_stats = db.session.execute(text(sql_user_stats), {"user_id": user_id})
review_count = result_stats.fetchone()[0]

sql_user_works = "SELECT id, title FROM works WHERE user_id = :user_id"
result_works = db.session.execute(text(sql_user_works), {"user_id": user_id})
works = result_works.fetchall()



query_string = "%" + query + "%"
sql_search = "SELECT id, title FROM works WHERE title ILIKE :query OR description ILIKE :query"
result = db.session.execute(text(sql_search), {"query": query_string})
search_results = result.fetchall()
