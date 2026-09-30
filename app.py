import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from db_helper import db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "moviemagic_secret_key_2026_super_secure")

@app.context_processor
def inject_user():
    user = session.get("user")
    available_locations = ["New York", "Los Angeles", "Chicago", "San Francisco", "Seattle", "Austin"]
    available_genres = ["All", "Sci-Fi", "Action", "Fantasy", "Musical", "Thriller", "Drama", "Event"]
    return dict(
        current_user=user, 
        locations=available_locations, 
        genres=available_genres,
        is_aws_mode=db.use_aws_dynamodb
    )

# ------------------ FRONTEND ROUTES ------------------

@app.route("/")
def index():
    selected_location = request.args.get("location", "New York")
    selected_genre = request.args.get("genre", "All")
    search_query = request.args.get("search", "").strip()

    movies = db.get_movies(
        location=selected_location if selected_location != "All" else None,
        genre=selected_genre if selected_genre != "All" else None,
        search=search_query if search_query else None
    )

    # Separate movies and special live events
    regular_movies = [m for m in movies if not m.get("is_event")]
    live_events = [m for m in movies if m.get("is_event")]

    return render_template(
        "index.html",
        movies=regular_movies,
        live_events=live_events,
        selected_location=selected_location,
        selected_genre=selected_genre,
        search_query=search_query
    )

@app.route("/movie/<movie_id>")
def movie_detail(movie_id):
    movie = db.get_movie_by_id(movie_id)
    if not movie:
        flash("Movie not found!", "danger")
        return redirect(url_for("index"))
    
    # Get recent reviews or similar movies
    all_movies = db.get_movies(location=movie.get("location"))
    similar_movies = [m for m in all_movies if m["movie_id"] != movie_id][:3]

    return render_template("movie_detail.html", movie=movie, similar_movies=similar_movies)

@app.route("/movie/<movie_id>/select-seats")
def select_seats(movie_id):
    if "user" not in session:
        flash("Please log in to select seats and book tickets.", "warning")
        return redirect(url_for("login", next=request.url))

    movie = db.get_movie_by_id(movie_id)
    if not movie:
        flash("Movie not found!", "danger")
        return redirect(url_for("index"))

    # Get occupied seats for this movie
    occupied_seats = db.get_booked_seats_for_movie(movie_id)

    return render_template("seat_selection.html", movie=movie, occupied_seats=occupied_seats)

@app.route("/api/book-seats", methods=["POST"])
def book_seats_api():
    if "user" not in session:
        return jsonify({"success": False, "message": "Authentication required. Please log in."}), 401

    data = request.get_json() or {}
    movie_id = data.get("movie_id")
    seats = data.get("seats", [])
    location = data.get("location")
    booking_date = data.get("booking_date")

    if not movie_id or not seats:
        return jsonify({"success": False, "message": "Invalid movie selection or no seats chosen."}), 400

    user_id = session["user"]["user_id"]

    try:
        booking = db.create_booking(
            user_id=user_id,
            movie_id=movie_id,
            seat_numbers=seats,
            location=location,
            booking_date=booking_date
        )
        return jsonify({
            "success": True,
            "message": "Booking successful!",
            "booking_id": booking["booking_id"],
            "redirect_url": url_for("booking_confirmation", booking_id=booking["booking_id"])
        })
    except ValueError as err:
        return jsonify({"success": False, "message": str(err)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

@app.route("/booking/<booking_id>")
def booking_confirmation(booking_id):
    if "user" not in session:
        flash("Please log in to view booking details.", "warning")
        return redirect(url_for("login"))

    user_id = session["user"]["user_id"]
    bookings = db.get_bookings()
    target_booking = None
    for b in bookings:
        if b["booking_id"] == booking_id and (b["user_id"] == user_id or session["user"].get("role") == "admin"):
            target_booking = b
            break

    if not target_booking:
        flash("Booking record not found or access denied.", "danger")
        return redirect(url_for("my_bookings"))

    movie = db.get_movie_by_id(target_booking["movie_id"])
    notifications = db.get_user_notifications(user_id)
    notif = next((n for n in notifications if n.get("booking_id") == booking_id), None)

    return render_template(
        "booking_confirmation.html",
        booking=target_booking,
        movie=movie,
        notification=notif
    )

@app.route("/my-bookings")
def my_bookings():
    if "user" not in session:
        flash("Please log in to view your bookings.", "warning")
        return redirect(url_for("login"))

    user_id = session["user"]["user_id"]
    user_bookings = db.get_bookings(user_id=user_id)
    return render_template("my_bookings.html", bookings=user_bookings)

@app.route("/cancel-booking/<booking_id>", methods=["POST"])
def cancel_booking(booking_id):
    if "user" not in session:
        flash("Unauthorized action.", "danger")
        return redirect(url_for("login"))

    user_id = session["user"]["user_id"]
    success = db.cancel_booking(booking_id, user_id)
    if success:
        flash(f"Booking {booking_id} has been successfully cancelled.", "success")
    else:
        flash(f"Could not cancel booking {booking_id}.", "danger")
    return redirect(url_for("my_bookings"))

# ------------------ AUTHENTICATION ------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        user = db.find_user_by_username(username)
        if not user:
            # Also allow login with email
            user = db.find_user_by_email(username)

        if user and user["password"] == password:
            session["user"] = {
                "user_id": user["user_id"],
                "username": user["username"],
                "email": user["email"],
                "role": user.get("role", "user")
            }
            flash(f"Welcome back, {user['username']}!", "success")
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if db.find_user_by_username(username):
            flash("Username already taken. Please choose another.", "warning")
            return render_template("register.html")

        if db.find_user_by_email(email):
            flash("An account with this email already exists.", "warning")
            return render_template("register.html")

        new_user = db.create_user(username, email, password)
        session["user"] = {
            "user_id": new_user["user_id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "role": new_user["role"]
        }
        flash("Registration successful! Welcome to Movie Magic.", "success")
        return redirect(url_for("index"))

    return render_template("register.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# ------------------ ADMIN DASHBOARD ------------------

@app.route("/admin")
def admin():
    if "user" not in session or session["user"].get("role") != "admin":
        flash("Admin privileges required to access this page.", "danger")
        return redirect(url_for("index"))

    all_movies = db.get_movies()
    all_bookings = db.get_bookings()
    all_users = db.get_users()
    all_notifications = db.local_data.get("notifications", [])

    return render_template(
        "admin.html",
        movies=all_movies,
        bookings=all_bookings,
        users=all_users,
        notifications=all_notifications
    )

@app.route("/admin/add-movie", methods=["POST"])
def admin_add_movie():
    if "user" not in session or session["user"].get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    title = request.form.get("title")
    genre = request.form.get("genre")
    language = request.form.get("language", "English")
    duration = request.form.get("duration", "2h 00m")
    show_time = request.form.get("show_time", "19:00")
    total_seats = int(request.form.get("total_seats", 60))
    location = request.form.get("location", "New York")
    price = float(request.form.get("price", 15.00))
    rating = request.form.get("rating", "4.8 ★")
    poster_url = request.form.get("poster_url") or "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=800&auto=format&fit=crop"
    description = request.form.get("description", "Exciting movie experience.")
    is_event = request.form.get("is_event") == "on"

    movie_data = {
        "title": title,
        "genre": genre,
        "language": language,
        "duration": duration,
        "show_time": show_time,
        "total_seats": total_seats,
        "available_seats": total_seats,
        "location": location,
        "price": price,
        "rating": rating,
        "poster_url": poster_url,
        "description": description,
        "is_event": is_event,
        "director": request.form.get("director", "Unknown Director"),
        "cast": request.form.get("cast", "Starring Cast")
    }

    db.add_movie(movie_data)
    flash(f"Movie/Event '{title}' added successfully!", "success")
    return redirect(url_for("admin"))

@app.route("/admin/toggle-aws", methods=["POST"])
def toggle_aws_mode():
    if "user" not in session or session["user"].get("role") != "admin":
        return jsonify({"success": False, "message": "Unauthorized"}), 403

    db.use_aws_dynamodb = not db.use_aws_dynamodb
    mode_str = "AWS DynamoDB Cloud Mode" if db.use_aws_dynamodb else "Local In-Memory Mode"
    flash(f"Switched system storage mode to: {mode_str}", "info")
    return redirect(url_for("admin"))

# ------------------ API NOTIFICATION LOGS ------------------

@app.route("/api/user-notifications")
def get_user_notifications_api():
    if "user" not in session:
        return jsonify([])
    user_id = session["user"]["user_id"]
    notifs = db.get_user_notifications(user_id)
    return jsonify(notifs)

if __name__ == "__main__":
    print("Starting Movie Magic Application on http://127.0.0.1:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)
