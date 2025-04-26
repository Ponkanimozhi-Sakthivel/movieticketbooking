from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movietickets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/movie_posters')

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    language = db.Column(db.String(50), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    poster_image = db.Column(db.String(200))
    genre = db.Column(db.String(100))
    rating = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Coming Soon')  # Now Showing, Coming Soon
    shows = db.relationship('Show', backref='movie', lazy=True)

class Theater(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    screens = db.relationship('Screen', backref='theater', lazy=True)

class Screen(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    theater_id = db.Column(db.Integer, db.ForeignKey('theater.id'), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    shows = db.relationship('Show', backref='screen', lazy=True)

class Show(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    screen_id = db.Column(db.Integer, db.ForeignKey('screen.id'), nullable=False)
    show_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    bookings = db.relationship('Booking', backref='show', lazy=True)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    seat_number = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), default='Available')  # Available, Booked, Reserved
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'), nullable=False)
    booking_time = db.Column(db.DateTime, default=datetime.utcnow)
    seats = db.relationship('Seat', backref='booking', lazy=True)
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Cancelled

# Create admin user
@app.before_first_request
def create_tables_and_admin():
    db.create_all()
    
    # Create admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
    
    # Create sample theaters and screens
    create_sample_theaters()

# Add this after your models but before your routes

def verify_admin_status(user_id):
    """Verify and fix admin status if needed"""
    user = User.query.get(user_id)
    if user and not user.is_admin:
        user.is_admin = True
        db.session.commit()
        return True
    return False

# Add this function after create_tables_and_admin()

def create_sample_theaters():
    """Create sample theaters and screens if they don't exist"""
    if not Theater.query.first():
        # Create theaters
        theaters = [
            {
                'name': 'PVR Cinemas',
                'location': 'Phoenix Mall',
                'capacity': 500,
                'screens': [
                    {'name': 'IMAX Screen', 'capacity': 250},
                    {'name': '4DX Screen', 'capacity': 150},
                    {'name': 'Gold Class Screen', 'capacity': 100}
                ]
            },
            {
                'name': 'INOX',
                'location': 'Central Mall',
                'capacity': 560,
                'screens': [
                    {'name': 'Premium Screen 1', 'capacity': 180},
                    {'name': 'Premium Screen 2', 'capacity': 180},
                    {'name': 'Regular Screen', 'capacity': 200}
                ]
            },
            {
                'name': 'Cinepolis',
                'location': 'City Centre',
                'capacity': 520,
                'screens': [
                    {'name': 'VIP Screen', 'capacity': 120},
                    {'name': 'Standard Screen 1', 'capacity': 200},
                    {'name': 'Standard Screen 2', 'capacity': 200}
                ]
            }
        ]

        try:
            for theater_data in theaters:
                theater = Theater(
                    name=theater_data['name'],
                    location=theater_data['location'],
                    capacity=theater_data['capacity']
                )
                db.session.add(theater)
                db.session.flush()  # Get theater ID

                for screen_data in theater_data['screens']:
                    screen = Screen(
                        name=screen_data['name'],
                        capacity=screen_data['capacity'],
                        theater_id=theater.id
                    )
                    db.session.add(screen)
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error creating sample theaters: {str(e)}")

# Routes
@app.route('/')
def index():
    now_showing = Movie.query.filter_by(status='Now Showing').all()
    coming_soon = Movie.query.filter_by(status='Coming Soon').all()
    return render_template('index.html', now_showing=now_showing, coming_soon=coming_soon)

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    shows = Show.query.filter_by(movie_id=movie_id)\
                     .filter(Show.show_time > datetime.now())\
                     .order_by(Show.show_time).all()
    return render_template('movie_detail.html', movie=movie, shows=shows)

@app.route('/book/<int:show_id>', methods=['GET', 'POST'])
def book_tickets(show_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login to book tickets'})
    
    if request.method == 'POST':
        seat_numbers = request.form.getlist('seats[]')
        if not seat_numbers:
            return jsonify({'success': False, 'message': 'Please select at least one seat'})
        
        try:
            # Start transaction
            db.session.begin()
            
            # Lock the show first
            show = Show.query.filter_by(id=show_id).with_for_update().first()
            if not show:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'Show not found'})

            # Get and lock available seats
            available_seats = Seat.query.filter(
                Seat.show_id == show_id,
                Seat.seat_number.in_(seat_numbers),
                Seat.status == 'Available'
            ).with_for_update().all()

            # Verify seat availability
            if len(available_seats) != len(seat_numbers):
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Some selected seats are no longer available. Please try again.'
                })

            try:
                # Create booking
                booking = Booking(
                    user_id=session['user_id'],
                    show_id=show_id,
                    status='Confirmed',
                    booking_time=datetime.now()
                )
                db.session.add(booking)
                db.session.flush()  # Get booking ID

                # Update seats status
                for seat in available_seats:
                    seat.status = 'Booked'
                    seat.booking_id = booking.id

                # Update show's available seats
                show.available_seats -= len(available_seats)
                
                # Commit transaction
                db.session.commit()
                return jsonify({
                    'success': True,
                    'redirect': url_for('booking_confirmation', booking_id=booking.id)
                })

            except Exception as e:
                db.session.rollback()
                print(f"Booking creation error: {str(e)}")
                return jsonify({
                    'success': False,
                    'message': 'Error creating booking. Please try again.'
                })

        except Exception as e:
            db.session.rollback()
            print(f"Seat verification error: {str(e)}")
            return jsonify({
                'success': False,
                'message': 'Error processing booking. Please try again.'
            })
    
    # GET request
    show = Show.query.get_or_404(show_id)
    seats = Seat.query.filter_by(show_id=show_id).all()
    return render_template('booking.html', show=show, seats=seats)

@app.route('/booking/<int:booking_id>')
def booking_confirmation(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != session['user_id'] and not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('index'))
    
    # Get seat numbers for this booking
    seats = [seat.seat_number for seat in booking.seats]
    
    return render_template('booking_confirmation.html', 
                         booking=booking,
                         seats=sorted(seats))

# Admin routes
@app.route('/admin/movies', methods=['GET', 'POST'])
def admin_movies():
    if not session.get('is_admin'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        duration = int(request.form['duration'])
        language = request.form['language']
        release_date = datetime.strptime(request.form['release_date'], '%Y-%m-%d')
        genre = request.form['genre']
        status = request.form['status']
        
        movie = Movie(
            title=title,
            description=description,
            duration=duration,
            language=language,
            release_date=release_date,
            genre=genre,
            status=status
        )
        
        if 'poster' in request.files:
            file = request.files['poster']
            if file:
                filename = f"{title.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}.jpg"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                movie.poster_image = filename
        
        db.session.add(movie)
        db.session.commit()
        flash('Movie added successfully', 'success')
        return redirect(url_for('admin_movies'))
    
    movies = Movie.query.all()
    return render_template('admin/movies.html', movies=movies)

@app.route('/admin/movies/delete/<int:movie_id>')
def delete_movie(movie_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    movie = Movie.query.get_or_404(movie_id)
    
    # Delete associated shows
    shows = Show.query.filter_by(movie_id=movie_id).all()
    for show in shows:
        # Delete associated seats
        Seat.query.filter_by(show_id=show.id).delete()
        # Delete associated bookings
        bookings = Booking.query.filter_by(show_id=show.id).all()
        for booking in bookings:
            db.session.delete(booking)
        db.session.delete(show)
    
    # Delete movie poster if exists
    if movie.poster_image:
        poster_path = os.path.join(app.config['UPLOAD_FOLDER'], movie.poster_image)
        if os.path.exists(poster_path):
            os.remove(poster_path)
    
    db.session.delete(movie)
    db.session.commit()
    flash('Movie deleted successfully', 'success')
    return redirect(url_for('admin_movies'))

# Add this route after the delete_movie route

@app.route('/admin/movies/edit/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        movie.title = request.form['title']
        movie.description = request.form['description']
        movie.duration = int(request.form['duration'])
        movie.language = request.form['language']
        movie.release_date = datetime.strptime(request.form['release_date'], '%Y-%m-%d')
        movie.genre = request.form['genre']
        movie.status = request.form['status']
        
        if 'poster' in request.files:
            file = request.files['poster']
            if file and file.filename:
                # Delete old poster if exists
                if movie.poster_image:
                    old_poster = os.path.join(app.config['UPLOAD_FOLDER'], movie.poster_image)
                    if os.path.exists(old_poster):
                        os.remove(old_poster)
                
                # Save new poster
                filename = f"{movie.title.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}.jpg"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                movie.poster_image = filename
        
        try:
            db.session.commit()
            flash('Movie updated successfully', 'success')
            return redirect(url_for('admin_movies'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating movie', 'danger')
            return render_template('admin/edit_movie.html', movie=movie)
    
    return render_template('admin/edit_movie.html', movie=movie)

from datetime import datetime

@app.route('/admin/shows', methods=['GET', 'POST'])
def admin_shows():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    movies = Movie.query.all()
    theaters = Theater.query.all()
    screens = Screen.query.join(Theater).all()  # Get all screens with their theaters
    shows = Show.query.order_by(Show.show_time).all()
    
    if request.method == 'POST':
        movie_id = request.form['movie_id']
        screen_id = request.form['screen_id']
        
        # Validate screen_id
        screen = Screen.query.get(screen_id)
        if not screen:
            flash('Invalid screen selected', 'danger')
            return render_template('admin/shows.html', 
                                movies=movies, 
                                theaters=theaters,
                                screens=screens,  # Pass screens to template
                                shows=shows,
                                now=datetime.now())
        
        try:
            show_time = datetime.strptime(
                f"{request.form['show_date']} {request.form['show_time']}", 
                '%Y-%m-%d %H:%M'
            )
            price = float(request.form['price'])
            
            # Check if show_time is in the future
            if show_time <= datetime.now():
                flash('Show time must be in the future', 'danger')
                return render_template('admin/shows.html', 
                                    movies=movies, 
                                    theaters=theaters,
                                    screens=screens,  # Pass screens to template
                                    shows=shows,
                                    now=datetime.now())
            
            # Check for conflicting shows on the same screen
            conflicting_show = Show.query.filter_by(screen_id=screen_id)\
                .filter(Show.show_time.between(
                    show_time - timedelta(hours=3),
                    show_time + timedelta(hours=3)
                )).first()
            
            if conflicting_show:
                flash('There is already a show scheduled at this time on this screen', 'danger')
                return render_template('admin/shows.html', 
                                    movies=movies, 
                                    theaters=theaters,
                                    screens=screens,  # Pass screens to template
                                    shows=shows,
                                    now=datetime.now())
            
            show = Show(
                movie_id=movie_id,
                screen_id=screen_id,
                show_time=show_time,
                price=price,
                available_seats=screen.capacity
            )
            
            db.session.add(show)
            db.session.flush()  # Get show ID

            # Create seats for the show
            rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
            seats_per_row = min(screen.capacity // len(rows), 10)  # Max 10 seats per row

            for row in rows:
                for num in range(1, seats_per_row + 1):
                    seat = Seat(
                        show_id=show.id,
                        seat_number=f"{row}{num}",
                        status='Available'
                    )
                    db.session.add(seat)

            db.session.commit()
            flash('Show added successfully', 'success')
            
        except ValueError as e:
            flash('Invalid date or time format', 'danger')
        except Exception as e:
            db.session.rollback()
            flash('Error adding show', 'danger')
        
        return redirect(url_for('admin_shows'))
    
    return render_template('admin/shows.html', 
                         movies=movies, 
                         theaters=theaters,
                         screens=screens,  # Pass screens to template
                         shows=shows,
                         now=datetime.now())

# Add this route after the admin_shows route

@app.route('/admin/shows/delete/<int:show_id>')
def delete_show(show_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    show = Show.query.get_or_404(show_id)
    
    try:
        # Delete associated seats
        Seat.query.filter_by(show_id=show_id).delete()
        
        # Delete associated bookings
        bookings = Booking.query.filter_by(show_id=show_id).all()
        for booking in bookings:
            db.session.delete(booking)
        
        # Delete the show
        db.session.delete(show)
        db.session.commit()
        
        flash('Show deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting show', 'danger')
    
    return redirect(url_for('admin_shows'))

@app.route('/admin/shows/add', methods=['POST'])
def add_show():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    try:
        movie_id = request.form.get('movie_id')
        screen_id = request.form.get('screen_id')
        show_time = datetime.strptime(request.form.get('show_time'), '%Y-%m-%dT%H:%M')
        price = float(request.form.get('price'))

        # Create show
        show = Show(
            movie_id=movie_id,
            screen_id=screen_id,
            show_time=show_time,
            price=price,
            available_seats=100  # Initialize with total seats
        )
        db.session.add(show)
        db.session.flush()  # To get the show.id

        # Create seats for the show (10 rows x 10 seats)
        for row in 'ABCDEFGHIJ':
            for num in range(1, 11):
                seat = Seat(
                    show_id=show.id,
                    seat_number=f"{row}{num}",
                    status='Available'
                )
                db.session.add(seat)

        db.session.commit()
        flash('Show added successfully', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding show: {str(e)}', 'danger')

    return redirect(url_for('admin_shows'))

# Add this function to initialize seats for existing shows
def initialize_seats_for_show(show_id):
    show = Show.query.get(show_id)
    if not show:
        return False
    
    try:
        # Check if seats already exist
        existing_seats = Seat.query.filter_by(show_id=show_id).count()
        if existing_seats > 0:
            return True

        # Create seats for the show
        for row in 'ABCDEFGHIJ':
            for num in range(1, 11):
                seat = Seat(
                    show_id=show_id,
                    seat_number=f"{row}{num}",
                    status='Available'
                )
                db.session.add(seat)
        
        show.available_seats = 100  # 10x10 seats
        db.session.commit()
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error initializing seats: {str(e)}")
        return False

@app.route('/admin/bookings')
def admin_bookings():
    if not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    # Get all bookings with joined data
    bookings = Booking.query\
        .join(Show)\
        .join(Movie)\
        .join(Screen)\
        .join(Theater)\
        .join(User)\
        .order_by(Booking.booking_time.desc())\
        .all()

    # Group bookings by movie
    bookings_by_movie = {}
    for booking in bookings:
        movie_title = booking.show.movie.title
        if movie_title not in bookings_by_movie:
            bookings_by_movie[movie_title] = {
                'bookings': [],
                'total_amount': 0,
                'total_seats': 0
            }
        bookings_by_movie[movie_title]['bookings'].append(booking)
        bookings_by_movie[movie_title]['total_amount'] += booking.show.price * len(booking.seats)
        bookings_by_movie[movie_title]['total_seats'] += len(booking.seats)

    # Group by theater
    bookings_by_theater = {}
    for booking in bookings:
        theater_name = booking.show.screen.theater.name
        if theater_name not in bookings_by_theater:
            bookings_by_theater[theater_name] = {
                'bookings': [],
                'total_amount': 0,
                'total_seats': 0
            }
        bookings_by_theater[theater_name]['bookings'].append(booking)
        bookings_by_theater[theater_name]['total_amount'] += booking.show.price * len(booking.seats)
        bookings_by_theater[theater_name]['total_seats'] += len(booking.seats)

    # Group by date
    bookings_by_date = {}
    for booking in bookings:
        booking_date = booking.show.show_time.date()
        if booking_date not in bookings_by_date:
            bookings_by_date[booking_date] = {
                'bookings': [],
                'total_amount': 0,
                'total_seats': 0
            }
        bookings_by_date[booking_date]['bookings'].append(booking)
        bookings_by_date[booking_date]['total_amount'] += booking.show.price * len(booking.seats)
        bookings_by_date[booking_date]['total_seats'] += len(booking.seats)

    return render_template('admin/bookings.html',
                         bookings=bookings,
                         bookings_by_movie=bookings_by_movie,
                         bookings_by_theater=bookings_by_theater,
                         bookings_by_date=bookings_by_date)

@app.route('/admin/bookings/cancel/<int:booking_id>')
def admin_cancel_booking(booking_id):
    if not session.get('is_admin'):
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    try:
        # Update booking status
        booking.status = 'Cancelled'
        
        # Release the seats
        for seat in booking.seats:
            seat.status = 'Available'
            seat.booking_id = None
        
        # Update show's available seats
        booking.show.available_seats += len(booking.seats)
        
        db.session.commit()
        flash('Booking cancelled successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error cancelling booking', 'danger')
    
    return redirect(url_for('admin_bookings'))

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # Verify admin status
            if user.is_admin:
                verify_admin_status(user.id)
            
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Logged in successfully', 'success')
            return redirect(url_for('admin_movies' if user.is_admin else 'index'))
        flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

ADMIN_REGISTRATION_CODE = "roohithbala"  # Change this to a secure code

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone')  # Optional field
        
        # Validate password
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return redirect(url_for('register'))
        
        # Check if user already exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('register'))
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            phone=phone,
            is_admin=False
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'danger')
            return redirect(url_for('register'))
    
    return render_template('register.html', admin_registration=False)

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        admin_code = request.form.get('admin_code')
        phone = request.form.get('phone')
        
        # Validate data
        if not all([username, email, password, admin_code]):
            flash('All fields are required', 'danger')
            return redirect(url_for('admin_register'))
        
        # Check if user exists
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return redirect(url_for('admin_register'))
        
        # Verify admin code
        if admin_code != ADMIN_REGISTRATION_CODE:
            flash('Invalid admin registration code', 'danger')
            return redirect(url_for('admin_register'))
        
        try:
            # Create admin user with explicit is_admin=True
            admin = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                phone=phone,
                is_admin=True  # Explicitly set to True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            # Double-check if admin status was set
            created_admin = User.query.filter_by(username=username).first()
            if not created_admin.is_admin:
                created_admin.is_admin = True
                db.session.commit()
            
            flash('Admin registration successful! Please login.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during admin registration: {str(e)}")  # For debugging
            flash('An error occurred during registration', 'danger')
            return redirect(url_for('admin_register'))
    
    return render_template('register.html', admin_registration=True)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to view your bookings', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(session['user_id'])
    bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.booking_time.desc()).all()
    
    return render_template('dashboard.html', user=user, bookings=bookings)

def initialize_all_shows():
    with app.app_context():
        shows = Show.query.all()
        for show in shows:
            initialize_seats_for_show(show.id)
        print("Initialized seats for all shows")

# Add this to your if __name__ == '__main__': block
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        initialize_all_shows()  # Initialize seats for existing shows
    app.run(debug=True)