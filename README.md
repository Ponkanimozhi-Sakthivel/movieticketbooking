# Movie Ticket Booking System

A web-based movie ticket booking system built with Flask and SQLAlchemy that allows users to book movie tickets online.

## Features

- User Authentication (Login/Register)
- Movie Listings with Details
- Show Schedule Management
- Seat Selection Interface
- Real-time Seat Availability
- Secure Booking Process
- Admin Dashboard
- Booking History

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite/MySQL
- **Frontend**: HTML, CSS, JavaScript
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/movie-ticket-booking.git
cd movie-ticket-booking
```

2. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

5. Run the application:
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## Project Structure

```
DBMS/
├── Python/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   │   ├── admin/
│   │   └── html files
│   ├── app.py
│   ├── models.py
│   └── requirements.txt
└── README.md
```

## Database Schema

- **Users**: User information and authentication
- **Movies**: Movie details and metadata
- **Shows**: Show timings and screen information
- **Seats**: Seat mapping and availability
- **Bookings**: Booking records and status

## API Endpoints

- `/login` - User authentication
- `/register` - New user registration
- `/movies` - List all movies
- `/book/<show_id>` - Book tickets for a show
- `/admin/*` - Admin panel routes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask documentation
- SQLAlchemy documentation
- Bootstrap templates