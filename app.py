from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import json
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hostel_crm.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ============== DATABASE MODELS ==============

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    is_admin = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RoomType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(7), default='#e8e4dc')
    base_price = db.Column(db.Float, default=0)
    capacity = db.Column(db.Integer, default=2)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rooms = db.relationship('Room', backref='room_type', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=False)
    floor = db.Column(db.String(10), default='1')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    bookings = db.relationship('Booking', backref='room', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), nullable=False)
    guest_email = db.Column(db.String(120))
    guest_phone = db.Column(db.String(20))
    guest_id = db.Column(db.String(50))
    id_type = db.Column(db.String(20), default='passport')

    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)

    booking_type = db.Column(db.String(20), default='walkin')
    source = db.Column(db.String(30), default='manual')

    total_price = db.Column(db.Float, default=0)
    amount_paid = db.Column(db.Float, default=0)
    payment_status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(20), default='cash')

    status = db.Column(db.String(20), default='confirmed')
    notes = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class DailyPrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_type_id = db.Column(db.Integer, db.ForeignKey('room_type.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    price = db.Column(db.Float, nullable=False)

    __table_args__ = (db.UniqueConstraint('room_type_id', 'date', name='unique_daily_price'),)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(30), nullable=False)
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============== AUTHENTICATION ==============

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============== ROUTES ==============

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() or request.form
        username = data.get('username', '').strip()
        password = data.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return jsonify({'success': True, 'redirect': url_for('dashboard')})

        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    email = data.get('email', '').strip()

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 400

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(user)
    db.session.commit()

    login_user(user)
    return jsonify({'success': True, 'redirect': url_for('dashboard')})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    google_id = data.get('googleId')

    if not email or not google_id:
        return jsonify({'success': False, 'message': 'Invalid Google data'}), 400

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
        else:
            username = name.replace(' ', '_').lower() if name else email.split('@')[0]
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                google_id=google_id,
                password_hash=generate_password_hash(os.urandom(24).hex())
            )
            db.session.add(user)
        db.session.commit()

    login_user(user)
    return jsonify({'success': True, 'redirect': url_for('dashboard')})

# ============== MAIN PAGES ==============

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

@app.route('/rooms')
@login_required
def rooms_page():
    return render_template('rooms.html')

@app.route('/bookings')
@login_required
def bookings_page():
    return render_template('bookings.html')

@app.route('/guests')
@login_required
def guests_page():
    return render_template('guests.html')

@app.route('/settings')
@login_required
def settings_page():
    return render_template('settings.html')

# ============== API ENDPOINTS ==============

@app.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Today's stats
    today_checkins = Booking.query.filter(Booking.check_in == today).count()
    today_checkouts = Booking.query.filter(Booking.check_out == today).count()
    today_staying = Booking.query.filter(
        Booking.check_in <= today,
        Booking.check_out > today,
        Booking.status == 'confirmed'
    ).count()

    # Revenue
    today_revenue = db.session.query(db.func.sum(Booking.amount_paid)).filter(
        db.func.date(Booking.created_at) == today
    ).scalar() or 0

    week_revenue = db.session.query(db.func.sum(Booking.amount_paid)).filter(
        Booking.created_at >= week_start
    ).scalar() or 0

    month_revenue = db.session.query(db.func.sum(Booking.amount_paid)).filter(
        Booking.created_at >= month_start
    ).scalar() or 0

    # Occupancy
    total_rooms = Room.query.filter_by(status='active').count()
    occupied_today = Booking.query.filter(
        Booking.check_in <= today,
        Booking.check_out > today,
        Booking.status == 'confirmed'
    ).count()
    occupancy_rate = round((occupied_today / total_rooms * 100), 1) if total_rooms > 0 else 0

    # Booking sources
    sources = db.session.query(
        Booking.source,
        db.func.count(Booking.id),
        db.func.sum(Booking.total_price)
    ).filter(
        Booking.created_at >= month_start
    ).group_by(Booking.source).all()

    # Weekly data for chart
    weekly_data = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_revenue = db.session.query(db.func.sum(Booking.amount_paid)).filter(
            db.func.date(Booking.created_at) == day
        ).scalar() or 0
        day_bookings = Booking.query.filter(db.func.date(Booking.created_at) == day).count()
        weekly_data.append({
            'day': day.strftime('%a'),
            'date': day.strftime('%Y-%m-%d'),
            'revenue': float(day_revenue),
            'bookings': day_bookings
        })

    return jsonify({
        'today': {
            'checkins': today_checkins,
            'checkouts': today_checkouts,
            'staying': today_staying,
            'revenue': float(today_revenue)
        },
        'revenue': {
            'today': float(today_revenue),
            'week': float(week_revenue),
            'month': float(month_revenue)
        },
        'occupancy': {
            'rate': occupancy_rate,
            'occupied': occupied_today,
            'total': total_rooms
        },
        'sources': [{'name': s[0], 'count': s[1], 'revenue': float(s[2] or 0)} for s in sources],
        'weekly_chart': weekly_data
    })

@app.route('/api/room-types', methods=['GET', 'POST'])
@login_required
def room_types_api():
    if request.method == 'POST':
        data = request.get_json()
        rt = RoomType(
            name=data['name'],
            color=data.get('color', '#e8e4dc'),
            base_price=data.get('base_price', 0),
            capacity=data.get('capacity', 2),
            description=data.get('description', '')
        )
        db.session.add(rt)
        db.session.commit()
        return jsonify({'success': True, 'id': rt.id})

    types = RoomType.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'color': t.color,
        'base_price': t.base_price,
        'capacity': t.capacity,
        'description': t.description
    } for t in types])

@app.route('/api/rooms', methods=['GET', 'POST'])
@login_required
def rooms_api():
    if request.method == 'POST':
        data = request.get_json()
        room = Room(
            name=data['name'],
            room_type_id=data['room_type_id'],
            floor=data.get('floor', '1'),
            status=data.get('status', 'active')
        )
        db.session.add(room)
        db.session.commit()
        return jsonify({'success': True, 'id': room.id})

    rooms = Room.query.all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'room_type_id': r.room_type_id,
        'room_type_name': r.room_type.name if r.room_type else '',
        'floor': r.floor,
        'status': r.status,
        'color': r.room_type.color if r.room_type else '#e8e4dc'
    } for r in rooms])

@app.route('/api/bookings', methods=['GET', 'POST'])
@login_required
def bookings_api():
    if request.method == 'POST':
        data = request.get_json()
        booking = Booking(
            guest_name=data['guest_name'],
            guest_email=data.get('guest_email', ''),
            guest_phone=data.get('guest_phone', ''),
            guest_id=data.get('guest_id', ''),
            id_type=data.get('id_type', 'passport'),
            room_id=data['room_id'],
            check_in=datetime.strptime(data['check_in'], '%Y-%m-%d').date(),
            check_out=datetime.strptime(data['check_out'], '%Y-%m-%d').date(),
            booking_type=data.get('booking_type', 'walkin'),
            source=data.get('source', 'manual'),
            total_price=data.get('total_price', 0),
            amount_paid=data.get('amount_paid', 0),
            payment_status=data.get('payment_status', 'pending'),
            payment_method=data.get('payment_method', 'cash'),
            status=data.get('status', 'confirmed'),
            notes=data.get('notes', ''),
            created_by=current_user.id
        )
        db.session.add(booking)
        db.session.commit()
        return jsonify({'success': True, 'id': booking.id})

    bookings = Booking.query.order_by(Booking.check_in.desc()).all()
    return jsonify([{
        'id': b.id,
        'guest_name': b.guest_name,
        'guest_email': b.guest_email,
        'guest_phone': b.guest_phone,
        'guest_id': b.guest_id,
        'id_type': b.id_type,
        'room_id': b.room_id,
        'room_name': b.room.name if b.room else '',
        'check_in': b.check_in.strftime('%Y-%m-%d'),
        'check_out': b.check_out.strftime('%Y-%m-%d'),
        'booking_type': b.booking_type,
        'source': b.source,
        'total_price': b.total_price,
        'amount_paid': b.amount_paid,
        'payment_status': b.payment_status,
        'payment_method': b.payment_method,
        'status': b.status,
        'notes': b.notes,
        'nights': (b.check_out - b.check_in).days
    } for b in bookings])

@app.route('/api/bookings/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def booking_detail(id):
    booking = Booking.query.get_or_404(id)

    if request.method == 'PUT':
        data = request.get_json()
        booking.guest_name = data.get('guest_name', booking.guest_name)
        booking.guest_email = data.get('guest_email', booking.guest_email)
        booking.guest_phone = data.get('guest_phone', booking.guest_phone)
        booking.guest_id = data.get('guest_id', booking.guest_id)
        booking.room_id = data.get('room_id', booking.room_id)
        if 'check_in' in data:
            booking.check_in = datetime.strptime(data['check_in'], '%Y-%m-%d').date()
        if 'check_out' in data:
            booking.check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()
        booking.booking_type = data.get('booking_type', booking.booking_type)
        booking.source = data.get('source', booking.source)
        booking.total_price = data.get('total_price', booking.total_price)
        booking.amount_paid = data.get('amount_paid', booking.amount_paid)
        booking.payment_status = data.get('payment_status', booking.payment_status)
        booking.payment_method = data.get('payment_method', booking.payment_method)
        booking.status = data.get('status', booking.status)
        booking.notes = data.get('notes', booking.notes)

        db.session.commit()
        return jsonify({'success': True})

    if request.method == 'DELETE':
        booking.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/calendar-data')
@login_required
def calendar_data():
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    if not start_date or not end_date:
        today = date.today()
        start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        end_date = (today + timedelta(days=21)).strftime('%Y-%m-%d')

    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()

    rooms = Room.query.filter_by(status='active').all()
    bookings = Booking.query.filter(
        Booking.check_in < end,
        Booking.check_out > start,
        Booking.status == 'confirmed'
    ).all()

    # Generate date range
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    room_data = []
    for room in rooms:
        room_bookings = []
        for b in bookings:
            if b.room_id == room.id:
                room_bookings.append({
                    'id': b.id,
                    'guest_name': b.guest_name,
                    'check_in': b.check_in.strftime('%Y-%m-%d'),
                    'check_out': b.check_out.strftime('%Y-%m-%d'),
                    'booking_type': b.booking_type,
                    'source': b.source,
                    'payment_status': b.payment_status,
                    'total_price': b.total_price,
                    'amount_paid': b.amount_paid,
                    'nights': (b.check_out - b.check_in).days
                })

        room_data.append({
            'id': room.id,
            'name': room.name,
            'room_type_id': room.room_type_id,
            'room_type_name': room.room_type.name if room.room_type else '',
            'color': room.room_type.color if room.room_type else '#e8e4dc',
            'bookings': room_bookings
        })

    return jsonify({
        'dates': dates,
        'rooms': room_data
    })

@app.route('/api/prices', methods=['GET', 'POST'])
@login_required
def prices_api():
    if request.method == 'POST':
        data = request.get_json()
        for item in data:
            existing = DailyPrice.query.filter_by(
                room_type_id=item['room_type_id'],
                date=datetime.strptime(item['date'], '%Y-%m-%d').date()
            ).first()

            if existing:
                existing.price = item['price']
            else:
                dp = DailyPrice(
                    room_type_id=item['room_type_id'],
                    date=datetime.strptime(item['date'], '%Y-%m-%d').date(),
                    price=item['price']
                )
                db.session.add(dp)

        db.session.commit()
        return jsonify({'success': True})

    room_type_id = request.args.get('room_type_id')
    start = request.args.get('start')
    end = request.args.get('end')

    query = DailyPrice.query
    if room_type_id:
        query = query.filter_by(room_type_id=room_type_id)
    if start and end:
        query = query.filter(
            DailyPrice.date >= datetime.strptime(start, '%Y-%m-%d').date(),
            DailyPrice.date <= datetime.strptime(end, '%Y-%m-%d').date()
        )

    prices = query.all()
    return jsonify([{
        'id': p.id,
        'room_type_id': p.room_type_id,
        'date': p.date.strftime('%Y-%m-%d'),
        'price': p.price
    } for p in prices])

@app.route('/api/extend-booking/<int:id>', methods=['POST'])
@login_required
def extend_booking(id):
    data = request.get_json()
    new_check_out = datetime.strptime(data['check_out'], '%Y-%m-%d').date()

    booking = Booking.query.get_or_404(id)
    booking.check_out = new_check_out

    if 'additional_price' in data:
        booking.total_price += data['additional_price']

    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/confirm-payment/<int:id>', methods=['POST'])
@login_required
def confirm_payment(id):
    data = request.get_json()
    booking = Booking.query.get_or_404(id)

    amount = data.get('amount', booking.total_price - booking.amount_paid)
    booking.amount_paid += amount

    if booking.amount_paid >= booking.total_price:
        booking.payment_status = 'paid'
    else:
        booking.payment_status = 'partial'

    db.session.commit()
    return jsonify({'success': True, 'new_status': booking.payment_status})

# ============== INITIAL SETUP ==============

def init_db():
    with app.app_context():
        db.create_all()

        # Create default admin if no users exist
        if not User.query.first():
            admin = User(
                username='admin',
                email='admin@hostel.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)

            # Create default room types
            types = [
                RoomType(name='Dormitory', color='#d4e6f1', base_price=150000, capacity=8, description='Shared dormitory beds'),
                RoomType(name='Private Single', color='#d5f5e3', base_price=300000, capacity=1, description='Private single room'),
                RoomType(name='Private Double', color='#fdebd0', base_price=450000, capacity=2, description='Private room with double bed'),
                RoomType(name='Family Room', color='#f5b7b1', base_price=600000, capacity=4, description='Room for families')
            ]
            for t in types:
                db.session.add(t)

            db.session.commit()

            # Create sample rooms
            rooms = [
                Room(name='A1', room_type_id=1, floor='1'),
                Room(name='A2', room_type_id=1, floor='1'),
                Room(name='A3', room_type_id=1, floor='1'),
                Room(name='B1', room_type_id=2, floor='1'),
                Room(name='B2', room_type_id=2, floor='1'),
                Room(name='C1', room_type_id=3, floor='2'),
                Room(name='C2', room_type_id=3, floor='2'),
                Room(name='D1', room_type_id=4, floor='2')
            ]
            for r in rooms:
                db.session.add(r)

            db.session.commit()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
