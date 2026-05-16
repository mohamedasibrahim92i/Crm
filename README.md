# 🏨 Hostel CRM - 

A complete, lightweight, and mobile-friendly Property Management System (PMS) built specifically for hostels in Indonesia. Designed for easy self-hosting with minimal technical knowledge.

## ✨ Features

### Core PMS
- **📅 Interactive Calendar View** - Drag-and-drop style booking grid with rooms on the left and dates across the top
- **🛏️ Room & Bed Management** - Manage room types, individual rooms, and capacity
- **📋 Booking Management** - Create, edit, extend, and cancel bookings
- **👥 Guest Directory** - Track guest history, preferences, and contact info
- **💰 Payment Tracking** - Record payments, track balances, confirm payments

### OTA Integration Ready
- **🔗 Channel Manager Framework** - Pre-built structure for Booking.com, Agoda, Traveloka, TripAdvisor, and Hostelworld APIs
- **🎨 Color-Coded Sources** - Instantly distinguish bookings by source (Booking.com = blue, Agoda = purple, etc.)
- **📊 Source Analytics** - Track which channels drive your revenue

### Dashboard & Analytics
- **📈 Real-time Dashboard** - Today's check-ins, check-outs, occupancy, and revenue
- **📊 Weekly Charts** - Revenue and booking trends with Chart.js
- **🥧 Source Distribution** - Pie chart showing booking channel breakdown
- **📉 Occupancy Gauge** - Visual occupancy rate indicator
- **📋 Performance Metrics** - ADR, RevPAR, and occupancy statistics

### Mobile-First Design
- **📱 Responsive Layout** - Works perfectly on phones, tablets, and desktops
- **⚡ Fast Loading** - Minimal dependencies, optimized for slow connections
- **🌙 Off-White Theme** - Easy on the eyes for long front-desk shifts

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

### 3. Access the System
Open your browser to: `http://localhost:5000`

**Default Login:**
- Username: `admin`
- Password: `admin123`

### 4. Google Sign-In (Optional)
To enable Google login:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Replace `YOUR_GOOGLE_CLIENT_ID` in `templates/login.html`

## 🏗️ Project Structure

```
hostel-crm/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── hostel_crm.db         # SQLite database (auto-created)
├── README.md
└── templates/
    ├── base.html         # Base layout with sidebar
    ├── login.html       # Login page with Google OAuth
    ├── dashboard.html   # Analytics dashboard
    ├── calendar.html    # Main booking calendar
    ├── bookings.html    # All bookings list
    ├── rooms.html       # Room management
    ├── guests.html      # Guest directory
    └── settings.html    # Configuration page
```

## 🔌 OTA Integration Setup

### Booking.com
1. Apply for [Booking.com Connectivity Partner Program](https://partner.booking.com/)
2. Get your API credentials
3. Add to environment variables:
```bash
export BOOKINGCOM_API_KEY="your_key"
export BOOKINGCOM_HOTEL_ID="your_hotel_id"
```

### Agoda
1. Register as [Agoda Partner](https://partnerhub.agoda.com/)
2. Request API access through their connectivity program [^26^]
3. Use their Full Content API for complete property management [^25^]

### Traveloka
1. Contact Traveloka Partner Support
2. Request API integration credentials

### Hostelworld
1. Access [Hostelworld Extranet](https://extranet.hostelworld.com/)
2. Request channel manager API access

### Implementation
Add sync functions to `app.py`:
```python
@app.route('/api/sync/bookingcom')
def sync_bookingcom():
    # Fetch bookings from Booking.com API
    # Import to local database
    pass
```

## 🎨 Customization

### Colors
Edit room type colors in the calendar:
- Go to **Rooms & Types** page
- Each room type has a unique color
- All bookings from that room type inherit the color

### Pricing
Set daily prices:
1. Click **Set Prices** on calendar page
2. Select room type and date range
3. Enter price per night

### Currency
Default is **IDR (Indonesian Rupiah)**. Change in Settings page.

## 📱 Mobile Usage

The system is fully responsive:
- **Swipe** the calendar horizontally on mobile
- **Tap** any empty cell to add a booking
- **Tap** any booking bar to view/edit details
- **Sidebar** slides in from left on mobile

## 🔒 Security

- Password hashing with Werkzeug
- Session-based authentication
- CSRF protection ready
- SQLite database (easy backup)

## 💾 Backup

The database is a single file: `hostel_crm.db`

**To backup:**
```bash
cp hostel_crm.db hostel_crm_backup_$(date +%Y%m%d).db
```

## 🌐 Deployment Options

### PythonAnywhere (Free)
1. Upload files to PythonAnywhere
2. Create a web app with Flask
3. Done!

### DigitalOcean / VPS
```bash
git clone <your-repo>
cd hostel-crm
pip install -r requirements.txt
python app.py
```

Use `screen` or `systemd` to keep it running.

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## 📊 Industry Standards

This system follows 2026 hostel PMS best practices [^1^]:
- Bed-level inventory management
- Pooled inventory model for OTAs [^18^]
- Real-time 2-way sync architecture
- Mobile-first guest experience
- Integrated payment tracking

## 🆘 Support

For issues or feature requests:
1. Check the Settings page for configuration
2. Review the code in `app.py`
3. The system is designed to be simple enough to modify

## 📄 License

MIT License - Free for commercial use.

---

**Built with ❤️ for hostels in Yogyakarta, Indonesia**
