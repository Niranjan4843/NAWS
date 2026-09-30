import os
import sys
import unittest

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
from db_helper import db

class MovieMagicTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        db.local_data["bookings"] = []
        db._save_local_data()

    def test_01_index_page(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'MovieMagic', response.data)
        self.assertIn(b'Cyberpunk Odyssey', response.data)

    def test_02_location_and_genre_filtering(self):
        response = self.app.get('/?location=New+York&genre=Sci-Fi')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Cyberpunk Odyssey', response.data)

    def test_03_login(self):
        response = self.app.post('/login', data={
            'username': 'alex_johnson',
            'password': 'Password123!'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'alex_johnson', response.data)

    def test_04_seat_booking_and_sns(self):
        # First log in
        with self.app.session_transaction() as sess:
            sess['user'] = {
                'user_id': 'USR-1001',
                'username': 'alex_johnson',
                'email': 'alex.johnson@example.com',
                'role': 'user'
            }

        booking_payload = {
            'movie_id': 'MOV-101',
            'seats': ['B3', 'B4'],
            'location': 'New York',
            'booking_date': '2026-10-01'
        }

        res = self.app.post('/api/book-seats', json=booking_payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('booking_id', data)

        booking_id = data['booking_id']
        conf_res = self.app.get(f'/booking/{booking_id}')
        self.assertEqual(conf_res.status_code, 200)
        self.assertIn(b'Booking Confirmed', conf_res.data)
        self.assertIn(b'B3, B4', conf_res.data)

    def test_05_admin_dashboard(self):
        with self.app.session_transaction() as sess:
            sess['user'] = {
                'user_id': 'USR-9999',
                'username': 'admin',
                'email': 'admin@moviemagic.com',
                'role': 'admin'
            }
        res = self.app.get('/admin')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'System Administrator Control Panel', res.data)

if __name__ == '__main__':
    unittest.main()
