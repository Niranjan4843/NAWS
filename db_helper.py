import os
import json
import uuid
import datetime
from typing import Dict, List, Optional, Any

# Try importing boto3 for AWS DynamoDB & SNS integration
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

DATA_FILE = os.path.join(os.path.dirname(__file__), "data_store.json")

# Default Initial Data (Epic 1 requirement: local data structures for rapid testing)
DEFAULT_MOVIES = [
    {
        "movie_id": "MOV-101",
        "title": "Cyberpunk Odyssey",
        "genre": "Sci-Fi",
        "language": "English",
        "duration": "2h 25m",
        "show_time": "18:30",
        "available_seats": 42,
        "total_seats": 60,
        "location": "New York",
        "price": 18.50,
        "rating": "4.9 ★",
        "poster_url": "/static/images/poster_cyberpunk.jpg",
        "description": "In a sprawling dystopian metropolis, a cybernetically enhanced mercenary embarks on a high-stakes mission across futuristic skylines to uncover a corporate conspiracy.",
        "is_event": False,
        "director": "Denis Villeneuve",
        "cast": "Jessica Chen, Kairo Reed, Marcus Vance"
    },
    {
        "movie_id": "MOV-102",
        "title": "The Cosmic Mystery",
        "genre": "Sci-Fi",
        "language": "English",
        "duration": "2h 10m",
        "show_time": "20:00",
        "available_seats": 35,
        "total_seats": 50,
        "location": "Los Angeles",
        "price": 20.00,
        "rating": "4.8 ★",
        "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=800&auto=format&fit=crop",
        "description": "An interstellar exploration crew discovers an ancient alien signal coming from the edge of the solar system, revealing secrets that could reshape human history.",
        "is_event": False,
        "director": "Christopher Nolan",
        "cast": "Matthew Miller, Anne Hathaway, John David"
    },
    {
        "movie_id": "MOV-103",
        "title": "Kingdom of Legends",
        "genre": "Fantasy",
        "language": "English",
        "duration": "2h 45m",
        "show_time": "19:15",
        "available_seats": 28,
        "total_seats": 60,
        "location": "Chicago",
        "price": 16.50,
        "rating": "4.7 ★",
        "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800&auto=format&fit=crop",
        "description": "A mythical tale of ancient kingdoms, fire-breathing dragons, and an unexpected hero bound by destiny to unite a divided empire.",
        "is_event": False,
        "director": "Peter Jackson",
        "cast": "Elijah Wood, Ian McKellen, Viggo Mortensen"
    },
    {
        "movie_id": "MOV-104",
        "title": "Starlight Symphony Live",
        "genre": "Musical",
        "language": "English",
        "duration": "3h 00m",
        "show_time": "21:00",
        "available_seats": 50,
        "total_seats": 100,
        "location": "New York",
        "price": 35.00,
        "rating": "5.0 ★",
        "poster_url": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?q=80&w=800&auto=format&fit=crop",
        "description": "An exclusive live orchestra performance featuring legendary soundtracks from timeless cinema blockbusters with light and laser spectacles.",
        "is_event": True,
        "director": "Hans Zimmer Production",
        "cast": "London Philharmonic & Guests"
    },
    {
        "movie_id": "MOV-105",
        "title": "Shadows of Yesterday",
        "genre": "Thriller",
        "language": "English",
        "duration": "1h 55m",
        "show_time": "17:45",
        "available_seats": 18,
        "total_seats": 45,
        "location": "San Francisco",
        "price": 15.00,
        "rating": "4.6 ★",
        "poster_url": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?q=80&w=800&auto=format&fit=crop",
        "description": "A detective haunted by a unsolved case receives mysterious clues that point to a crime committed 20 years ago in his hometown.",
        "is_event": False,
        "director": "David Fincher",
        "cast": "Jake Gyllenhaal, Mark Ruffalo"
    },
    {
        "movie_id": "MOV-106",
        "title": "Global Tech & Film Summit 2026",
        "genre": "Event",
        "language": "English",
        "duration": "5h 00m",
        "show_time": "10:00",
        "available_seats": 85,
        "total_seats": 150,
        "location": "San Francisco",
        "price": 50.00,
        "rating": "4.9 ★",
        "poster_url": "https://images.unsplash.com/photo-1540575467063-178a50c2df87?q=80&w=800&auto=format&fit=crop",
        "description": "A premier convergence of tech innovators and visual film creators exploring AI, cloud rendering, and immersive cinema tech.",
        "is_event": True,
        "director": "Tech Cinema Org",
        "cast": "Keynote Speakers & Filmmakers"
    }
]

DEFAULT_USERS = [
    {
        "user_id": "USR-1001",
        "username": "alex_johnson",
        "email": "alex.johnson@example.com",
        "password": "Password123!",
        "role": "user"
    },
    {
        "user_id": "USR-9999",
        "username": "admin",
        "email": "admin@moviemagic.com",
        "password": "AdminPassword123!",
        "role": "admin"
    }
]

class DatabaseManager:
    """
    Data management layer supporting both Local (File/In-Memory) storage
    and AWS DynamoDB cloud storage.
    """
    def __init__(self):
        self.use_aws_dynamodb = os.environ.get("USE_AWS_DYNAMODB", "false").lower() == "true"
        self.aws_region = os.environ.get("AWS_REGION", "us-east-1")
        self.sns_topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
        
        self.local_data = {
            "users": DEFAULT_USERS.copy(),
            "movies": DEFAULT_MOVIES.copy(),
            "bookings": [],
            "notifications": []
        }
        self._load_local_data()

    def _load_local_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    stored = json.load(f)
                    self.local_data.update(stored)
            except Exception as e:
                print(f"[DB] Error loading local data: {e}. Reverting to defaults.")
        else:
            self._save_local_data()

    def _save_local_data(self):
        try:
            with open(DATA_FILE, "w") as f:
                json.dump(self.local_data, f, indent=2)
        except Exception as e:
            print(f"[DB] Error saving local data: {e}")

    # ------------------ USERS ------------------
    def get_users(self) -> List[Dict]:
        if self.use_aws_dynamodb and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                table = dynamodb.Table('Users')
                response = table.scan()
                return response.get('Items', [])
            except Exception as e:
                print(f"[AWS DynamoDB Scan Error]: {e}. Falling back to local.")
        return self.local_data["users"]

    def find_user_by_username(self, username: str) -> Optional[Dict]:
        users = self.get_users()
        for u in users:
            if u["username"].lower() == username.lower():
                return u
        return None

    def find_user_by_email(self, email: str) -> Optional[Dict]:
        users = self.get_users()
        for u in users:
            if u["email"].lower() == email.lower():
                return u
        return None

    def create_user(self, username: str, email: str, password: str, role: str = "user") -> Dict:
        user_id = f"USR-{uuid.uuid4().hex[:6].upper()}"
        user_obj = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "password": password,
            "role": role,
            "created_at": datetime.datetime.now().isoformat()
        }
        
        if self.use_aws_dynamodb and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                table = dynamodb.Table('Users')
                table.put_item(Item=user_obj)
            except Exception as e:
                print(f"[AWS DynamoDB Create User Error]: {e}")
        
        # Always maintain local sync
        self.local_data["users"].append(user_obj)
        self._save_local_data()
        return user_obj

    # ------------------ MOVIES & EVENTS ------------------
    def get_movies(self, location: str = None, genre: str = None, search: str = None) -> List[Dict]:
        movies = self.local_data["movies"]
        if self.use_aws_dynamodb and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                table = dynamodb.Table('Movies')
                response = table.scan()
                items = response.get('Items', [])
                if items:
                    movies = items
            except Exception as e:
                print(f"[AWS DynamoDB Scan Movies Error]: {e}")

        # Filtering
        filtered = movies
        if location and location.lower() != "all":
            filtered = [m for m in filtered if m.get("location", "").lower() == location.lower()]
        if genre and genre.lower() != "all":
            filtered = [m for m in filtered if m.get("genre", "").lower() == genre.lower()]
        if search:
            q = search.lower()
            filtered = [m for m in filtered if q in m.get("title", "").lower() or q in m.get("description", "").lower()]
            
        return filtered

    def get_movie_by_id(self, movie_id: str) -> Optional[Dict]:
        if self.use_aws_dynamodb and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                table = dynamodb.Table('Movies')
                res = table.get_item(Key={'movie_id': movie_id})
                if 'Item' in res:
                    return res['Item']
            except Exception as e:
                print(f"[AWS DynamoDB Get Movie Error]: {e}")

        for m in self.local_data["movies"]:
            if m["movie_id"] == movie_id:
                return m
        return None

    def add_movie(self, movie_data: Dict) -> Dict:
        movie_id = f"MOV-{uuid.uuid4().hex[:6].upper()}"
        movie_data["movie_id"] = movie_id
        if "available_seats" not in movie_data:
            movie_data["available_seats"] = int(movie_data.get("total_seats", 50))
            
        if self.use_aws_dynamodb and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                table = dynamodb.Table('Movies')
                table.put_item(Item=movie_data)
            except Exception as e:
                print(f"[AWS DynamoDB Put Movie Error]: {e}")

        self.local_data["movies"].append(movie_data)
        self._save_local_data()
        return movie_data

    # ------------------ BOOKINGS & SEAT MANAGEMENT ------------------
    def get_bookings(self, user_id: str = None) -> List[Dict]:
        bookings = self.local_data["bookings"]
        if self.use_aws_dynamodb and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                table = dynamodb.Table('Bookings')
                res = table.scan()
                items = res.get('Items', [])
                if items:
                    bookings = items
            except Exception as e:
                print(f"[AWS DynamoDB Scan Bookings Error]: {e}")

        if user_id:
            bookings = [b for b in bookings if b.get("user_id") == user_id]
        
        # Sort by latest
        bookings.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return bookings

    def get_booked_seats_for_movie(self, movie_id: str) -> List[str]:
        """Returns all seats already booked for a specific movie."""
        bookings = self.get_bookings()
        occupied = []
        for b in bookings:
            if b.get("movie_id") == movie_id and b.get("status", "CONFIRMED") == "CONFIRMED":
                seats = b.get("seat_number", "")
                if isinstance(seats, list):
                    occupied.extend(seats)
                elif isinstance(seats, str):
                    occupied.extend([s.strip() for s in seats.split(",") if s.strip()])
        return occupied

    def create_booking(self, user_id: str, movie_id: str, seat_numbers: List[str], location: str, booking_date: str) -> Dict:
        movie = self.get_movie_by_id(movie_id)
        if not movie:
            raise ValueError("Movie or event not found.")

        current_occupied = self.get_booked_seats_for_movie(movie_id)
        for seat in seat_numbers:
            if seat in current_occupied:
                raise ValueError(f"Seat {seat} is already booked! Please select another seat.")

        num_seats = len(seat_numbers)
        unit_price = float(movie.get("price", 15.00))
        total_amount = round(num_seats * unit_price, 2)
        
        booking_id = f"BK-{uuid.uuid4().hex[:8].upper()}"
        seat_str = ", ".join(seat_numbers)
        
        booking_record = {
            "booking_id": booking_id,
            "user_id": user_id,
            "movie_id": movie_id,
            "movie_title": movie.get("title"),
            "location": location or movie.get("location"),
            "booking_date": booking_date or datetime.date.today().isoformat(),
            "show_time": movie.get("show_time", "19:00"),
            "seat_number": seat_str,
            "seat_count": num_seats,
            "total_amount": total_amount,
            "status": "CONFIRMED",
            "timestamp": datetime.datetime.now().isoformat()
        }

        # Deduct available seats
        new_avail = max(0, int(movie.get("available_seats", 50)) - num_seats)
        movie["available_seats"] = new_avail

        if self.use_aws_dynamodb and BOTO3_AVAILABLE:
            try:
                dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                # Save Booking
                b_table = dynamodb.Table('Bookings')
                b_table.put_item(Item=booking_record)
                # Update Movie available_seats
                m_table = dynamodb.Table('Movies')
                m_table.update_item(
                    Key={'movie_id': movie_id},
                    UpdateExpression="SET available_seats = :val",
                    ExpressionAttributeValues={':val': new_avail}
                )
            except Exception as e:
                print(f"[AWS DynamoDB Create Booking Error]: {e}")

        # Update local array
        self.local_data["bookings"].append(booking_record)
        # Update local movie object
        for m in self.local_data["movies"]:
            if m["movie_id"] == movie_id:
                m["available_seats"] = new_avail
                break
        self._save_local_data()

        # Trigger Notification (AWS SNS or Simulated SNS)
        self.send_booking_notification(booking_record)
        
        return booking_record

    def cancel_booking(self, booking_id: str, user_id: str) -> bool:
        for b in self.local_data["bookings"]:
            if b["booking_id"] == booking_id and (b["user_id"] == user_id or user_id == "USR-9999"):
                b["status"] = "CANCELLED"
                # Restore seats
                movie = self.get_movie_by_id(b["movie_id"])
                if movie:
                    movie["available_seats"] = int(movie.get("available_seats", 0)) + b.get("seat_count", 1)
                    if self.use_aws_dynamodb and BOTO3_AVAILABLE:
                        try:
                            dynamodb = boto3.resource('dynamodb', region_name=self.aws_region)
                            m_table = dynamodb.Table('Movies')
                            m_table.update_item(
                                Key={'movie_id': b["movie_id"]},
                                UpdateExpression="SET available_seats = :val",
                                ExpressionAttributeValues={':val': movie["available_seats"]}
                            )
                        except Exception as e:
                            print(f"[AWS DynamoDB Update Seat Error]: {e}")
                            
                self._save_local_data()
                return True
        return False

    # ------------------ AWS SNS NOTIFICATIONS ------------------
    def send_booking_notification(self, booking: Dict) -> Dict:
        """
        Sends AWS SNS notification when booking is created.
        Also creates a notification record in local memory for UI audit logs.
        """
        user = None
        for u in self.get_users():
            if u["user_id"] == booking["user_id"]:
                user = u
                break

        recipient_email = user["email"] if user else "customer@example.com"
        username = user["username"] if user else "Movie Enthusiast"

        subject = f"🎬 Ticket Confirmation: {booking['movie_title']} [Booking #{booking['booking_id']}]"
        message_body = f"""
Hello {username},

Your movie ticket booking is CONFIRMED! Here are your ticket details:

------------------------------------------------
Movie / Event : {booking['movie_title']}
Booking ID    : {booking['booking_id']}
Date & Time   : {booking['booking_date']} at {booking['show_time']}
Location      : {booking['location']}
Seats Booked  : {booking['seat_number']}
Total Paid    : ${booking['total_amount']:.2f}
Status        : CONFIRMED
------------------------------------------------

Thank you for choosing Movie Magic Cloud Ticket System!
Present your Booking ID or QR code at the theater entrance.

Best regards,
Movie Magic Team (Powered by AWS EC2 & DynamoDB)
"""

        sns_status = "SIMULATED_SUCCESS"
        aws_sns_message_id = None

        if BOTO3_AVAILABLE and self.sns_topic_arn:
            try:
                sns_client = boto3.client('sns', region_name=self.aws_region)
                response = sns_client.publish(
                    TopicArn=self.sns_topic_arn,
                    Subject=subject,
                    Message=message_body
                )
                aws_sns_message_id = response.get('MessageId')
                sns_status = "AWS_SNS_DELIVERED"
                print(f"[AWS SNS] Email published successfully. Message ID: {aws_sns_message_id}")
            except Exception as e:
                print(f"[AWS SNS Error]: {e}")
                sns_status = f"AWS_SNS_FAILED: {str(e)}"

        notif_record = {
            "notification_id": f"NOTIF-{uuid.uuid4().hex[:6].upper()}",
            "booking_id": booking['booking_id'],
            "user_id": booking['user_id'],
            "recipient_email": recipient_email,
            "subject": subject,
            "body": message_body,
            "status": sns_status,
            "aws_sns_message_id": aws_sns_message_id,
            "timestamp": datetime.datetime.now().isoformat()
        }

        self.local_data["notifications"].append(notif_record)
        self._save_local_data()
        return notif_record

    def get_user_notifications(self, user_id: str) -> List[Dict]:
        return [n for n in self.local_data.get("notifications", []) if n.get("user_id") == user_id]

# Singleton instance
db = DatabaseManager()
