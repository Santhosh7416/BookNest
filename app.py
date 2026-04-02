from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "secret123"

# MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["user_database"]

users = db["users"]
books = db["books"]
admins = db["admins"]
requests_collection = db["requests"]

# ---------------- LOGIN ----------------
@app.route("/")
def login():
    return render_template("login.html")

@app.route("/login_user", methods=["POST"])
def login_user():
    user = users.find_one({
        "username": request.form.get("username"),
        "password": request.form.get("password")
    })

    if user:
        session["user"] = user["username"]
        return redirect("/dashboard")
    return "Invalid Login"


# ---------------- REGISTER ----------------
@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/register_user", methods=["POST"])
def register_user():
    users.insert_one({
        "name": request.form.get("fullname"),
        "username": request.form.get("username"),
        "password": request.form.get("password"),
        "email": request.form.get("email")
    })
    return redirect("/")


# ---------------- USER DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    user = session["user"]

    my_books = list(books.find({"issued_to": user}))
    my_requests = list(
        requests_collection.find({"user": user}).sort("_id", -1)
    )

    return_requested = {}
    for req in my_requests:
        if req["type"] == "return" and req["status"] == "pending":
            return_requested[req["book_id"]] = True

    return render_template(
        "dashboard.html",
        user=user,
        my_books=my_books,
        my_requests=my_requests,
        return_requested=return_requested,
        total_books=books.count_documents({})
    )


# ---------------- VIEW BOOKS (USER SEARCH) ----------------
@app.route("/view_books")
def view_books():
    user = session.get("user")
    search_query = request.args.get("search", "").strip()

    # Book Search
    if search_query:
        all_books = list(books.find({
            "$or": [
                {"title": {"$regex": search_query, "$options": "i"}},
                {"author": {"$regex": search_query, "$options": "i"}}
            ]
        }))
    else:
        all_books = list(books.find())

    user_requests = list(
        requests_collection.find({"user": user}).sort("_id", -1)
    )

    book_status = {}
    request_ids = {}

    for req in user_requests:
        book_id = req["book_id"]

        if book_id in book_status:
            continue

        if req["type"] == "issue":
            if req["status"] == "pending":
                book_status[book_id] = "pending"
                request_ids[book_id] = str(req["_id"])
            elif req["status"] == "approved":
                book_status[book_id] = "issued"
            elif req["status"] == "rejected":
                book_status[book_id] = "none"

        elif req["type"] == "return":
            if req["status"] == "pending":
                book_status[book_id] = "return_pending"
            elif req["status"] == "approved":
                book_status[book_id] = "none"

    return render_template(
        "view_books.html",
        books=all_books,
        book_status=book_status,
        request_ids=request_ids,
        total_books=len(all_books),
        search_query=search_query
    )


# ---------------- REQUEST BOOK ----------------
@app.route("/request_book/<id>")
def request_book(id):
    user = session["user"]

    existing = requests_collection.find_one({
        "book_id": str(id),
        "user": user,
        "status": "pending",
        "type": "issue"
    })

    if existing:
        return "Already requested!"

    book = books.find_one({"_id": ObjectId(id)})

    requests_collection.insert_one({
        "book_id": str(id),
        "title": book["title"],
        "author": book["author"],
        "user": user,
        "status": "pending",
        "type": "issue"
    })

    return redirect("/view_books")


# ---------------- RETURN REQUEST ----------------
@app.route("/return_request/<id>")
def return_request(id):
    user = session["user"]

    existing = requests_collection.find_one({
        "book_id": str(id),
        "user": user,
        "status": "pending",
        "type": "return"
    })

    if existing:
        return "Return already requested!"

    book = books.find_one({"_id": ObjectId(id)})

    requests_collection.insert_one({
        "book_id": str(id),
        "title": book["title"],
        "author": book["author"],
        "user": user,
        "status": "pending",
        "type": "return"
    })

    return redirect("/dashboard")


# ---------------- CANCEL REQUEST ----------------
@app.route("/cancel_request/<id>")
def cancel_request(id):
    requests_collection.delete_one({"_id": ObjectId(id)})
    return redirect("/view_books")


# ---------------- ADMIN LOGIN ----------------
@app.route("/admin")
def admin():
    return render_template("admin_login.html")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    admin = admins.find_one({
        "username": request.form.get("username"),
        "password": request.form.get("password")
    })

    if admin:
        session["admin"] = True
        return redirect("/admin_dashboard")
    return "Invalid Admin Login"


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")

    search_user = request.args.get("search_user")
    search_book = request.args.get("search_book")

    open_sidebar = False

    # USER SEARCH
    if search_user:
        filtered_users = list(users.find({
            "username": {"$regex": search_user, "$options": "i"}
        }))
        open_sidebar = True
    else:
        filtered_users = list(users.find())

    # BOOK SEARCH
    if search_book:
        filtered_books = list(books.find({
            "$or": [
                {"title": {"$regex": search_book, "$options": "i"}},
                {"author": {"$regex": search_book, "$options": "i"}}
            ]
        }))
    else:
        filtered_books = list(books.find())

    # REQUESTS (FIXED)
    pending_requests = list(
        requests_collection.find({"status": "pending"}).sort("_id", -1)
    )

    return render_template(
        "admin_dashboard.html",
        books=filtered_books,
        users=filtered_users,
        requests=pending_requests,
        total_books=len(filtered_books),
        search_query=search_user,
        search_book=search_book,
        open_sidebar=open_sidebar
    )


# ---------------- ADD BOOK ----------------
@app.route("/add_book")
def add_book():
    return render_template("add_book.html")

@app.route("/add_book_data", methods=["POST"])
def add_book_data():
    books.insert_one({
        "title": request.form.get("title"),
        "author": request.form.get("author"),
        "stock": int(request.form.get("stock"))
    })
    return redirect("/admin_dashboard")


# ---------------- UPDATE STOCK ----------------
@app.route("/update_stock/<id>/<action>")
def update_stock(id, action):
    if action == "increase":
        books.update_one({"_id": ObjectId(id)}, {"$inc": {"stock": 1}})
    elif action == "decrease":
        books.update_one({"_id": ObjectId(id)}, {"$inc": {"stock": -1}})
    return redirect("/admin_dashboard")


# ---------------- DELETE BOOK ----------------
@app.route("/delete_book/<id>")
def delete_book(id):
    books.delete_one({"_id": ObjectId(id)})
    return redirect("/admin_dashboard")


# ---------------- DELETE USER ----------------

@app.route("/delete_user/<id>")
def delete_user(id):
    user = users.find_one({"_id": ObjectId(id)})
    return render_template("confirm_delete_user.html", user=user)

@app.route("/confirm_delete_user/<id>", methods=["POST"])
def confirm_delete_user(id):
    user = users.find_one({"_id": ObjectId(id)})

    entered_username = request.form.get("username")

    if entered_username == user["username"]:
        users.delete_one({"_id": ObjectId(id)})
        return redirect("/admin_dashboard")
    else:
        return render_template(
            "confirm_delete_user.html",
            user=user,
            error="❌ Username does not match!"
        )

# ---------------- APPROVE REQUEST ----------------
@app.route("/approve_request/<id>")
def approve_request(id):
    req = requests_collection.find_one({"_id": ObjectId(id)})
    book_id = ObjectId(req["book_id"])

    if req["type"] == "issue":
        books.update_one(
            {"_id": book_id},
            {
                "$inc": {"stock": -1},
                "$set": {"issued_to": req["user"]}
            }
        )

    elif req["type"] == "return":
        books.update_one(
            {"_id": book_id},
            {
                "$inc": {"stock": 1},
                "$unset": {"issued_to": ""}
            }
        )

    requests_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": "approved"}}
    )

    return redirect("/admin_dashboard")


# ---------------- REJECT REQUEST ----------------
@app.route("/reject_request/<id>")
def reject_request(id):
    requests_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"status": "rejected"}}
    )
    return redirect("/admin_dashboard")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)