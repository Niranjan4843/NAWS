# 🎬 Movie Magic - Cloud-Enabled Movie Ticket & Event Booking System

**Movie Magic** is a modern, full-stack Flask web application for booking movie tickets and live event passes. Built with dual-storage architecture, it seamlessly supports both **Local In-Memory / JSON storage** for offline testing and **AWS Cloud Services (DynamoDB & SNS)** for scalable production environments.

---

## ✨ Features

- 🍿 **Browse & Filter Movies/Events**: Search movies by title, filter by location (New York, Los Angeles, Chicago, etc.), and sort by genres (Sci-Fi, Action, Fantasy, Drama, Events).
- 🎟️ **Interactive Seat Selection Grid**: Dynamic graphical seat map showing real-time occupied vs. available seats.
- 🔐 **User Authentication & Authorization**: Secure user registration, login/logout, session tracking, and role-based access control (User vs. Admin).
- 🧾 **Booking Management & E-Tickets**: Instant booking confirmation with generated tickets, status tracking, and cancellation option.
- 📲 **AWS Cloud Notifications**: Automated ticket booking notifications powered by **AWS SNS (Simple Notification Service)**.
- ☁️ **Dual Database Architecture**: Switch dynamically between local JSON data store and **AWS DynamoDB** (`Users`, `Movies`, `Bookings` tables).
- 👑 **Admin Control Panel**: Add new movies/live events, manage bookings, review user records, and toggle live storage modes.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask
- **Frontend**: HTML5, CSS3, JavaScript, Jinja2 Templates, Bootstrap / FontAwesome
- **Cloud Infrastructure (AWS)**:
  - **AWS DynamoDB**: Scalable NoSQL database tables (`Users`, `Movies`, `Bookings`)
  - **AWS SNS**: Notification topic for instant ticket confirmations
  - **Boto3**: AWS SDK for Python
- **Database (Local Fallback)**: In-Memory JSON file data store (`data_store.json`)

---

## 📁 Project Structure

```text
├── app.py              # Main Flask application & routing controller
├── db_helper.py        # Database abstraction layer (DynamoDB + Local fallback)
├── aws_setup.py        # Automated AWS Cloud Infrastructure provisioning script
├── data_store.json     # Initial local dataset (movies, users, bookings)
├── templates/          # Jinja2 HTML templates
│   ├── base.html
│   ├── index.html
│   ├── movie_detail.html
│   ├── seat_selection.html
│   ├── booking_confirmation.html
│   ├── my_bookings.html
│   ├── login.html
│   ├── register.html
│   └── admin.html
└── static/             # Static CSS styles and frontend assets
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- `pip` package manager

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
cd NAWS
```

### 2. Install Dependencies

```bash
pip install flask boto3
```

---

## 🏃 Running the Application

### Option A: Running in Local Mode (Default - No AWS setup required)

Run the Flask development server:

```bash
python app.py
```

Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

### Option B: Running with AWS Cloud Mode (DynamoDB + SNS)

#### 1. Configure AWS Credentials
Ensure your AWS credentials are setup in your terminal or environment:

```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="us-east-1"
```

#### 2. Provision AWS Cloud Infrastructure
Run the infrastructure provisioning script to automatically create DynamoDB tables (`Users`, `Movies`, `Bookings`) and the SNS topic (`MovieMagic-BookingNotifications`):

```bash
python aws_setup.py
```

#### 3. Enable AWS Mode & Launch App

```bash
export USE_AWS_DYNAMODB=true
python app.py
```

*Note: You can also switch between Local and AWS Cloud Mode directly from the **Admin Dashboard** (`/admin`).*

---

## 🔐 Default Admin Account

- **Username**: `admin`
- **Password**: `admin123`

---

## 📜 License

This project is open-source and available under the **MIT License**.
