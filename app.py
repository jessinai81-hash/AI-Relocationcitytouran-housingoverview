"""
Relocation & Housing Concierge Agent
Flask backend for Abu Dhabi Relocation Platform
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import os
import json
import csv
import random
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "relocation_concierge_2024_abudhabi"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Vercel's filesystem is read-only except /tmp
if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/relocation.db"
else:
    DB_PATH = os.path.join(BASE_DIR, "database", "relocation.db")


# ---------------------------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            nationality TEXT,
            family_size INTEGER DEFAULT 1,
            budget INTEGER,
            preferred_community TEXT,
            property_type TEXT,
            move_date TEXT,
            employer TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS relocation_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_name TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS housing_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            community TEXT NOT NULL,
            property_type TEXT,
            bedrooms INTEGER,
            rent_annual INTEGER,
            rent_monthly INTEGER,
            size_sqft INTEGER,
            school_proximity_km REAL,
            hospital_proximity_km REAL,
            metro_access INTEGER DEFAULT 0,
            family_rating INTEGER DEFAULT 3,
            lifestyle_score INTEGER DEFAULT 3,
            description TEXT,
            amenities TEXT
        );

        CREATE TABLE IF NOT EXISTS temporary_housing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            location TEXT,
            price_per_night INTEGER,
            rating REAL,
            min_stay_days INTEGER DEFAULT 1,
            features TEXT,
            contact TEXT
        );

        CREATE TABLE IF NOT EXISTS airport_pickup (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            passenger_name TEXT NOT NULL,
            flight_number TEXT,
            arrival_date TEXT,
            arrival_time TEXT,
            terminal TEXT,
            luggage_count INTEGER DEFAULT 1,
            special_requirements TEXT,
            driver_name TEXT,
            vehicle TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS city_tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tour_name TEXT NOT NULL,
            category TEXT,
            duration_days INTEGER DEFAULT 1,
            description TEXT,
            highlights TEXT,
            best_for TEXT,
            estimated_cost_aed INTEGER
        );

        CREATE TABLE IF NOT EXISTS attractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            location TEXT,
            area TEXT,
            description TEXT,
            entry_fee_aed INTEGER DEFAULT 0,
            opening_hours TEXT,
            family_friendly INTEGER DEFAULT 1,
            rating REAL DEFAULT 4.0,
            tags TEXT
        );

        CREATE TABLE IF NOT EXISTS contact_inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            subject TEXT,
            message TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    _seed_data(c)
    conn.commit()
    conn.close()


def _seed_data(c):
    # Only seed if tables are empty
    c.execute("SELECT COUNT(*) FROM housing_options")
    if c.fetchone()[0] > 0:
        return

    # Housing options
    housing_rows = [
        ("Yas Island", "Apartment", 1, 65000, 5417, 750, 3.2, 4.1, 0, 4, 5, "Modern apartments near Ferrari World and Yas Mall", "Pool,Gym,Parking,Security"),
        ("Yas Island", "Apartment", 2, 95000, 7917, 1150, 3.2, 4.1, 0, 5, 5, "Spacious 2BR with island views and resort-style living", "Pool,Gym,Parking,Security,Kids Play"),
        ("Yas Island", "Villa", 3, 160000, 13333, 2200, 2.8, 4.1, 0, 5, 5, "Luxurious villa with private garden near Yas Beach", "Private Garden,Pool,Maid Room,BBQ,Parking"),
        ("Saadiyat Island", "Apartment", 2, 120000, 10000, 1300, 4.5, 5.0, 0, 4, 5, "Cultural district living near Louvre Abu Dhabi", "Beach Access,Pool,Gym,Concierge"),
        ("Saadiyat Island", "Villa", 4, 280000, 23333, 4500, 4.5, 5.0, 0, 5, 5, "Premium beachfront villa with world-class amenities", "Beach Access,Private Pool,Maid Room,Driver Room"),
        ("Al Reem Island", "Apartment", 1, 55000, 4583, 700, 2.1, 2.5, 1, 4, 4, "City-connected apartment with skyline views", "Pool,Gym,Metro Nearby,Parking"),
        ("Al Reem Island", "Apartment", 2, 80000, 6667, 1100, 2.1, 2.5, 1, 4, 4, "Popular family choice with school bus routes available", "Pool,Gym,School Nearby,Parking"),
        ("Al Reem Island", "Apartment", 3, 110000, 9167, 1600, 2.1, 2.5, 1, 5, 4, "Large family apartment with city and sea views", "Pool,Gym,BBQ Area,Parking"),
        ("Al Raha Beach", "Apartment", 2, 85000, 7083, 1200, 1.5, 3.0, 0, 5, 5, "Beachfront living with water canal views", "Beach Access,Pool,Gym,Marina"),
        ("Al Raha Beach", "Villa", 3, 170000, 14167, 2800, 1.5, 3.0, 0, 5, 5, "Townhouse with garden and beach club access", "Garden,Beach Club,Pool,Parking"),
        ("Khalifa City", "Villa", 3, 110000, 9167, 2500, 1.8, 3.5, 0, 5, 4, "Spacious suburban villa ideal for families", "Private Garden,Maid Room,Covered Parking,BBQ"),
        ("Khalifa City", "Villa", 4, 135000, 11250, 3200, 1.8, 3.5, 0, 5, 4, "Large family villa near American and British schools", "Private Garden,Maid Room,Study Room,Parking"),
        ("Mohammed Bin Zayed City", "Villa", 3, 90000, 7500, 2200, 2.0, 4.0, 0, 4, 3, "Affordable family villas with easy highway access", "Garden,Parking,Masjid Nearby"),
        ("Mohammed Bin Zayed City", "Villa", 4, 110000, 9167, 2800, 2.0, 4.0, 0, 4, 3, "Quiet residential community with supermarkets nearby", "Garden,Parking,Community Center"),
        ("Al Reef", "Apartment", 2, 50000, 4167, 950, 8.0, 7.0, 0, 4, 3, "Budget-friendly community with resort amenities", "Pool,Gym,Club House,Parking"),
        ("Al Reef", "Villa", 3, 75000, 6250, 1800, 8.0, 7.0, 0, 4, 3, "Affordable villa community with active lifestyle", "Pool,Gym,Sports Courts,Garden"),
        ("Masdar City", "Apartment", 1, 45000, 3750, 650, 5.0, 6.0, 0, 3, 3, "Eco-friendly sustainable community", "Smart Home,Solar Power,Gym,Parking"),
        ("Masdar City", "Apartment", 2, 65000, 5417, 950, 5.0, 6.0, 0, 3, 3, "Green living with advanced tech integration", "Smart Home,EV Charging,Pool,Gym"),
        ("Al Maryah Island", "Apartment", 1, 75000, 6250, 850, 1.0, 2.0, 1, 4, 5, "Financial district living near Galleria Mall", "Gym,Pool,Metro Nearby,Concierge"),
        ("Corniche Area", "Apartment", 2, 130000, 10833, 1400, 3.0, 2.5, 1, 4, 5, "Premium corniche living with sea views", "Sea View,Pool,Gym,Corniche Access"),
        ("Al Bateen", "Villa", 3, 160000, 13333, 2600, 2.5, 3.0, 0, 4, 4, "Prestigious embassy district residential area", "Garden,Maid Room,Parking,Quiet Area"),
        ("Al Mushrif", "Villa", 4, 130000, 10833, 3000, 3.0, 4.0, 0, 5, 4, "Family-oriented area near international schools", "Garden,Maid Room,Parking,Schools Nearby"),
        ("Al Shamkha", "Villa", 4, 80000, 6667, 2800, 12.0, 8.0, 0, 4, 3, "Affordable spacious villas with new infrastructure", "Large Garden,Parking,New Community"),
        ("Al Bahia", "Villa", 3, 70000, 5833, 2000, 15.0, 10.0, 0, 4, 3, "Up-and-coming community with sea views", "Sea View,Garden,Quiet,Parking"),
    ]
    c.executemany("""INSERT INTO housing_options
        (community, property_type, bedrooms, rent_annual, rent_monthly, size_sqft,
         school_proximity_km, hospital_proximity_km, metro_access, family_rating,
         lifestyle_score, description, amenities) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        housing_rows)

    # Temporary housing
    temp_rows = [
        ("Park Hyatt Abu Dhabi", "Hotel", "Saadiyat Island", 1200, 4.8, 1, "Beachfront,Spa,Multiple Restaurants,Pool", "+971-2-407-1234"),
        ("Jumeirah at Etihad Towers", "Hotel", "Corniche", 950, 4.7, 1, "Sea View,Pool,Gym,Fine Dining", "+971-2-811-5555"),
        ("Yas Island Rotana", "Hotel", "Yas Island", 550, 4.4, 1, "Pool,Gym,Near Ferrari World,Family Friendly", "+971-2-656-4000"),
        ("Marriott Hotel Al Forsan", "Hotel", "Khalifa City", 480, 4.3, 1, "Near Schools,Pool,Gym,Airport 15min", "+971-2-201-4000"),
        ("Fraser Suites Abu Dhabi", "Serviced Apartment", "Sheikh Zayed Street", 350, 4.5, 7, "Kitchen,Laundry,Pool,Gym,Long Stay Rates", "+971-2-659-0000"),
        ("Staybridge Suites Abu Dhabi", "Serviced Apartment", "Al Maryah Island", 420, 4.4, 7, "Full Kitchen,Living Room,Pool,Gym,Grocery", "+971-2-304-0000"),
        ("Citadines Metro Central Abu Dhabi", "Serviced Apartment", "Al Zahiyah", 280, 4.2, 7, "Kitchen,Laundry,Metro Nearby,Long Stay", "+971-2-410-0000"),
        ("Nation Riviera Beach Club Residences", "Serviced Apartment", "Corniche", 500, 4.6, 14, "Beachfront,Kitchen,Pool,Gym,Sea View", "+971-2-690-0000"),
        ("Mövenpick Hotel Bab Al Qasr", "Hotel", "Corniche", 650, 4.5, 1, "City View,Pool,Spa,Near Business District", "+971-2-204-4444"),
        ("Premier Inn Abu Dhabi International Airport", "Hotel", "Airport Area", 300, 4.1, 1, "Near Airport,Shuttle,Pool,Restaurant", "+971-2-505-0000"),
    ]
    c.executemany("""INSERT INTO temporary_housing
        (name, type, location, price_per_night, rating, min_stay_days, features, contact)
        VALUES (?,?,?,?,?,?,?,?)""", temp_rows)

    # City tours
    tours = [
        ("Classic 1-Day Abu Dhabi Highlights", "highlights", 1, "Experience Abu Dhabi's most iconic landmarks in a single day", "Sheikh Zayed Grand Mosque,Emirates Palace,Corniche,Heritage Village,Qasr Al Watan", "First-time visitors,Business travelers", 400),
        ("3-Day City Orientation Tour", "orientation", 3, "Comprehensive introduction to Abu Dhabi for new residents", "Grand Mosque,Corniche,Yas Island,Saadiyat,Al Maryah,Markets,Restaurants", "New residents,Expatriates", 900),
        ("7-Day Full Relocation Orientation", "orientation", 7, "Complete city familiarization for relocating families and executives", "All major areas,Schools,Hospitals,Supermarkets,Community tours,Cultural sites", "Relocating families,Corporate executives", 2500),
        ("Family Adventure Tour", "family", 2, "Designed for families with children, covering best family attractions", "Ferrari World,Yas Waterworld,SeaWorld,Warner Bros,Yas Mall,Corniche Beach", "Families with children", 800),
        ("Luxury Abu Dhabi Experience", "luxury", 2, "Premium experiences including private tours and fine dining", "Emirates Palace Tour,Louvre Abu Dhabi,Qasr Al Watan,Fine Dining,Desert Safari", "High-net-worth individuals,Luxury seekers", 3000),
        ("Cultural Heritage Tour", "cultural", 2, "Deep dive into Emirati culture, history and traditions", "Sheikh Zayed Grand Mosque,Heritage Village,Qasr Al Watan,Date Market,Gold Souk", "Culture enthusiasts,History buffs", 500),
        ("Weekend Explorer Tour", "weekend", 2, "Perfect weekend getaway covering beaches and entertainment", "Corniche Beach,Saadiyat Beach,Yas Beach,Mangrove Kayaking,Restaurants", "Weekend travelers,Beach lovers", 600),
        ("Shopping & Lifestyle Tour", "shopping", 1, "Discover Abu Dhabi's world-class shopping and dining scene", "Yas Mall,The Galleria,Marina Mall,World Trade Center,Local Markets", "Shopping enthusiasts", 300),
    ]
    c.executemany("""INSERT INTO city_tours
        (tour_name, category, duration_days, description, highlights, best_for, estimated_cost_aed)
        VALUES (?,?,?,?,?,?,?)""", tours)

    # Attractions
    attractions = [
        ("Sheikh Zayed Grand Mosque", "mosque", "Sheikh Zayed Street", "Corniche Area", "One of the world's largest mosques, architectural masterpiece of Islamic design", 0, "9:00 AM - 10:00 PM (Closed Fri morning)", 1, 4.9, "iconic,religious,architecture,free"),
        ("Louvre Abu Dhabi", "museum", "Saadiyat Island", "Saadiyat Island", "World-class art and civilization museum under a stunning dome", 63, "10:00 AM - 8:00 PM (Fri till 9 PM)", 1, 4.7, "art,culture,museum,world-class"),
        ("Ferrari World Abu Dhabi", "theme_park", "Yas Island", "Yas Island", "World's first Ferrari-branded theme park with record-breaking rides", 345, "11:00 AM - 8:00 PM", 1, 4.6, "thrill,family,ferrari,rides"),
        ("Warner Bros. World Abu Dhabi", "theme_park", "Yas Island", "Yas Island", "Immersive indoor theme park featuring DC and Looney Tunes", 330, "10:00 AM - 8:00 PM", 1, 4.6, "family,indoor,dc,looney-tunes"),
        ("Yas Waterworld", "water_park", "Yas Island", "Yas Island", "Arabia's biggest water park with 43 rides and slides", 285, "10:00 AM - 6:00 PM", 1, 4.5, "family,water,slides,thrill"),
        ("SeaWorld Abu Dhabi", "theme_park", "Yas Island", "Yas Island", "World's first SeaWorld without orca shows, ocean discovery park", 320, "10:00 AM - 8:00 PM", 1, 4.6, "marine,family,education,animals"),
        ("Qasr Al Watan", "palace", "Corniche", "Corniche Area", "Presidential Palace open to visitors, showcasing UAE heritage", 60, "10:00 AM - 8:00 PM", 1, 4.7, "palace,heritage,architecture,emirati"),
        ("Emirates Palace", "hotel", "Corniche", "Corniche Area", "Iconic ultra-luxury hotel, symbol of Abu Dhabi's opulence", 0, "Open to visitors for dining and tours", 1, 4.8, "luxury,iconic,hotel,gold"),
        ("Corniche Beach", "beach", "Corniche Road", "Corniche Area", "8km pristine beach along Abu Dhabi's stunning waterfront", 0, "24 Hours", 1, 4.5, "beach,free,family,walking"),
        ("Mangrove National Park", "nature", "Eastern Mangroves", "Eastern Abu Dhabi", "Unique mangrove ecosystem ideal for kayaking and birdwatching", 0, "Sunrise to Sunset", 1, 4.4, "nature,kayaking,wildlife,green"),
        ("Observation Deck at 300", "viewpoint", "Etihad Towers", "Corniche Area", "Stunning 360-degree views of Abu Dhabi from 74th floor", 75, "10:00 AM - 10:00 PM", 1, 4.4, "views,photography,skyline,iconic"),
        ("Heritage Village", "cultural", "Breakwater", "Corniche Area", "Open-air museum showcasing traditional Emirati way of life", 0, "9:00 AM - 4:00 PM (Closed Sat morning)", 1, 4.2, "free,culture,history,traditional"),
        ("Saadiyat Cultural District", "cultural", "Saadiyat Island", "Saadiyat Island", "Emerging cultural hub with world-class museums and galleries", 0, "Various hours per venue", 1, 4.5, "culture,arts,future,world-class"),
        ("Jubail Mangrove Park", "nature", "Jubail Island", "Eastern Abu Dhabi", "Peaceful mangrove boardwalk perfect for family nature walks", 0, "8:00 AM - 8:00 PM", 1, 4.6, "nature,free,family,peaceful"),
        ("Yas Marina Circuit", "sports", "Yas Island", "Yas Island", "Home of the Abu Dhabi Formula 1 Grand Prix, track tours available", 150, "Tours available daily", 1, 4.5, "f1,sport,racing,iconic"),
        ("The Galleria Al Maryah Island", "shopping", "Al Maryah Island", "Al Maryah Island", "Premium luxury shopping mall with over 400 stores", 0, "10:00 AM - 10:00 PM", 1, 4.5, "shopping,luxury,dining,family"),
        ("Yas Mall", "shopping", "Yas Island", "Yas Island", "Abu Dhabi's largest mall with 400+ stores and entertainment", 0, "10:00 AM - 10:00 PM", 1, 4.4, "shopping,family,cinema,dining"),
        ("Abu Dhabi Desert Safari", "adventure", "Al Ain Road Desert", "Outskirts", "Traditional desert experience with dune bashing and BBQ dinner", 250, "3:00 PM - 10:00 PM", 1, 4.6, "adventure,desert,cultural,bbq"),
        ("Yas Beach", "beach", "Yas Island", "Yas Island", "Pristine white sand beach with water sports and restaurants", 0, "9:00 AM - Sunset", 1, 4.3, "beach,sports,family,dining"),
        ("Abu Dhabi Golf Club", "sport", "Sas Al Nakhl Island", "Abu Dhabi", "Championship golf course hosting HSBC Abu Dhabi Golf Championship", 400, "Dawn to Dusk", 0, 4.5, "golf,sport,luxury,championship"),
    ]
    c.executemany("""INSERT INTO attractions
        (name, category, location, area, description, entry_fee_aed, opening_hours,
         family_friendly, rating, tags) VALUES (?,?,?,?,?,?,?,?,?,?)""", attractions)


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def generate_checklist_tasks(user_id, move_date_str=None):
    """Generate standard relocation checklist for a user."""
    tasks = [
        # Before Departure
        ("Apply for UAE Employment Visa", "Before Departure", "high"),
        ("Gather employment documentation and NOC letter", "Before Departure", "high"),
        ("Obtain international health insurance", "Before Departure", "high"),
        ("Research school options in preferred community", "Before Departure", "high"),
        ("Open international bank account or check UAE banking options", "Before Departure", "medium"),
        ("Arrange shipping / air freight for belongings", "Before Departure", "medium"),
        ("Notify current landlord / terminate lease", "Before Departure", "medium"),
        ("Update passport and get extra copies", "Before Departure", "high"),
        ("Get medical and vaccination records", "Before Departure", "medium"),
        ("Research UAE driving license requirements", "Before Departure", "low"),
        # After Arrival
        ("Apply for Emirates ID", "After Arrival", "high"),
        ("Get UAE mobile SIM card (Etisalat/du)", "After Arrival", "high"),
        ("Open UAE bank account (FAB/Emirates NBD/ADCB)", "After Arrival", "high"),
        ("Register with home country embassy", "After Arrival", "medium"),
        ("Set up DEWA utility account (if renting directly)", "After Arrival", "high"),
        ("Register children in school", "After Arrival", "high"),
        ("Obtain UAE driving license (or conversion)", "After Arrival", "medium"),
        ("Register with a GP/medical clinic", "After Arrival", "medium"),
        ("Set up internet connection (Etisalat/du)", "After Arrival", "high"),
        ("Explore neighborhood and locate nearest supermarket", "After Arrival", "low"),
        # Move-In
        ("Sign tenancy contract and get Ejari registration", "Move-In", "high"),
        ("Activate DEWA (electricity and water)", "Move-In", "high"),
        ("Arrange furniture delivery / purchase", "Move-In", "medium"),
        ("Set up internet and cable TV", "Move-In", "medium"),
        ("Register with community management (parking, access cards)", "Move-In", "high"),
        ("Set up AC maintenance contract", "Move-In", "medium"),
        ("Purchase home contents insurance", "Move-In", "low"),
        ("Meet neighbors and community manager", "Move-In", "low"),
    ]
    conn = get_db()
    c = conn.cursor()
    for task_name, category, priority in tasks:
        c.execute("""INSERT INTO relocation_checklists
            (user_id, task_name, category, status, priority) VALUES (?,?,?,'pending',?)""",
            (user_id, task_name, category, priority))
    conn.commit()
    conn.close()


def get_housing_recommendations(budget, family_size, preferred_community=None, property_type=None):
    """Return housing options matching criteria."""
    conn = get_db()
    c = conn.cursor()
    query = "SELECT * FROM housing_options WHERE rent_annual <= ?"
    params = [budget]
    if property_type and property_type != "any":
        query += " AND property_type = ?"
        params.append(property_type)
    if preferred_community and preferred_community != "any":
        query += " AND community = ?"
        params.append(preferred_community)
    if family_size:
        min_beds = max(1, int(family_size) // 2)
        query += " AND bedrooms >= ?"
        params.append(min_beds)
    query += " ORDER BY family_rating DESC, lifestyle_score DESC LIMIT 6"
    c.execute(query, params)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def generate_ai_summary(user_data):
    """Generate a personalized AI recommendation summary."""
    name = user_data.get("name", "the client")
    budget = user_data.get("budget", 100000)
    family_size = user_data.get("family_size", 1)
    community = user_data.get("preferred_community", "")
    property_type = user_data.get("property_type", "")
    employer = user_data.get("employer", "")

    # AI summary logic based on profile
    budget_tier = "premium" if budget > 180000 else ("mid-range" if budget > 90000 else "budget-friendly")
    family_type = "executive couple" if family_size <= 2 else ("family" if family_size <= 4 else "large family")

    community_recs = []
    if budget > 180000:
        community_recs = ["Saadiyat Island", "Yas Island", "Al Raha Beach"]
    elif budget > 110000:
        community_recs = ["Yas Island", "Al Reem Island", "Al Raha Beach", "Khalifa City"]
    elif budget > 70000:
        community_recs = ["Khalifa City", "Mohammed Bin Zayed City", "Al Reef", "Al Reem Island"]
    else:
        community_recs = ["Al Reef", "Masdar City", "Mohammed Bin Zayed City", "Al Shamkha"]

    summary = f"""Based on the relocation profile for **{name}**, our AI concierge has prepared the following personalized assessment:

**Profile Summary:** {family_type.title()} with a {budget_tier} annual housing budget of AED {budget:,}, relocating to Abu Dhabi{' with ' + employer if employer else ''}.

**Recommended Communities:** {', '.join(community_recs[:3])} offer the strongest alignment with your budget, lifestyle preferences, and family requirements.

**Housing Strategy:** {"A villa with private garden is recommended given the family size, providing space, privacy, and access to community amenities." if family_size > 3 else "A well-appointed apartment in a quality community provides an excellent balance of value, convenience, and lifestyle."}

**Temporary Accommodation:** We recommend a minimum 30-day serviced apartment stay upon arrival to allow adequate time for property viewings, school visits, and community exploration before committing to a long-term tenancy.

**Relocation Timeline:** {"Your move date allows ample preparation time. Begin school applications and visa processing immediately." if True else "Prioritize visa and documentation processing given the imminent move date."}

**Key Priorities:**
1. Emirates ID and residency visa processing (Days 1-14)
2. School enrollment for children (if applicable)
3. UAE bank account setup (FAB or Emirates NBD recommended)
4. Community orientation and property viewings (Days 15-30)
5. Tenancy contract and Ejari registration (Days 30-45)

**Abu Dhabi Welcome Note:** Abu Dhabi is consistently ranked among the world's safest and most livable cities. The expat community is vibrant and welcoming, and you will find excellent international schools, world-class healthcare, and a rich cultural scene to enjoy throughout your residency."""

    return summary


def generate_ai_relocation_score(user_data):
    """Calculate a relocation readiness score."""
    score = 70  # Base score
    budget = user_data.get("budget", 0)
    family_size = user_data.get("family_size", 1)
    move_date = user_data.get("move_date", "")

    if budget > 100000:
        score += 10
    if family_size <= 4:
        score += 5
    if move_date:
        try:
            move_dt = datetime.strptime(move_date, "%Y-%m-%d")
            days_until = (move_dt - datetime.now()).days
            if days_until > 60:
                score += 15
            elif days_until > 30:
                score += 8
        except Exception:
            pass

    return min(score, 100)


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    conn = get_db()
    stats = {
        "communities": conn.execute("SELECT COUNT(DISTINCT community) FROM housing_options").fetchone()[0],
        "properties": conn.execute("SELECT COUNT(*) FROM housing_options").fetchone()[0],
        "attractions": conn.execute("SELECT COUNT(*) FROM attractions").fetchone()[0],
        "tours": conn.execute("SELECT COUNT(*) FROM city_tours").fetchone()[0],
    }
    conn.close()
    return render_template("index.html", stats=stats)


@app.route("/relocation", methods=["GET", "POST"])
def relocation():
    if request.method == "POST":
        data = request.form
        conn = get_db()
        c = conn.cursor()
        c.execute("""INSERT INTO users
            (name, email, nationality, family_size, budget, preferred_community,
             property_type, move_date, employer)
            VALUES (?,?,?,?,?,?,?,?,?)""", (
            data.get("name"), data.get("email"), data.get("nationality"),
            int(data.get("family_size", 1)), int(data.get("budget", 80000)),
            data.get("preferred_community"), data.get("property_type"),
            data.get("move_date"), data.get("employer")
        ))
        user_id = c.lastrowid
        conn.commit()
        generate_checklist_tasks(user_id, data.get("move_date"))
        conn.close()
        flash(f"Welcome {data.get('name')}! Your relocation profile has been created.", "success")
        return redirect(url_for("relocation_profile", user_id=user_id))

    return render_template("relocation.html")


@app.route("/relocation/profile/<int:user_id>")
def relocation_profile(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return redirect(url_for("relocation"))
    checklist = conn.execute(
        "SELECT * FROM relocation_checklists WHERE user_id = ? ORDER BY category, priority DESC",
        (user_id,)
    ).fetchall()
    conn.close()

    # Organize checklist by category
    by_category = {}
    for item in checklist:
        cat = item["category"]
        by_category.setdefault(cat, []).append(dict(item))

    user_dict = dict(user)
    summary = generate_ai_summary(user_dict)
    score = generate_ai_relocation_score(user_dict)
    recommendations = get_housing_recommendations(
        user["budget"], user["family_size"],
        user["preferred_community"], user["property_type"]
    )

    return render_template("relocation_profile.html",
                           user=user_dict,
                           checklist=by_category,
                           summary=summary,
                           score=score,
                           recommendations=recommendations)


@app.route("/api/checklist/update", methods=["POST"])
def update_checklist():
    data = request.json
    conn = get_db()
    conn.execute("UPDATE relocation_checklists SET status = ? WHERE id = ?",
                 (data["status"], data["id"]))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/housing")
def housing():
    conn = get_db()
    communities_raw = conn.execute(
        "SELECT DISTINCT community FROM housing_options ORDER BY community"
    ).fetchall()
    communities = [r["community"] for r in communities_raw]

    all_housing = conn.execute(
        "SELECT * FROM housing_options ORDER BY community, bedrooms"
    ).fetchall()
    conn.close()

    housing_by_community = {}
    for h in all_housing:
        c = h["community"]
        housing_by_community.setdefault(c, []).append(dict(h))

    community_info = {
        "Yas Island": {"tagline": "Entertainment & Lifestyle Hub", "icon": "🏎️", "type": "Mixed Use Island"},
        "Saadiyat Island": {"tagline": "Culture & Luxury Beachfront", "icon": "🎨", "type": "Luxury Island"},
        "Al Reem Island": {"tagline": "Urban City Living", "icon": "🏙️", "type": "Urban Island"},
        "Al Raha Beach": {"tagline": "Waterfront Family Paradise", "icon": "⛵", "type": "Waterfront"},
        "Khalifa City": {"tagline": "Premier Family Suburb", "icon": "🏡", "type": "Suburban"},
        "Mohammed Bin Zayed City": {"tagline": "Spacious Residential Community", "icon": "🏘️", "type": "Suburban"},
        "Al Reef": {"tagline": "Affordable Resort Living", "icon": "🌴", "type": "Resort Community"},
        "Masdar City": {"tagline": "Smart Eco-Friendly Living", "icon": "♻️", "type": "Smart City"},
        "Al Maryah Island": {"tagline": "Financial District Hub", "icon": "💼", "type": "Business District"},
        "Corniche Area": {"tagline": "Premium Seafront Living", "icon": "🌊", "type": "Seafront"},
        "Al Bateen": {"tagline": "Prestigious Embassy District", "icon": "🏛️", "type": "Prestigious"},
        "Al Mushrif": {"tagline": "Family & Schools Proximity", "icon": "🎓", "type": "Family Area"},
        "Al Shamkha": {"tagline": "Modern Affordable Villas", "icon": "🏠", "type": "Suburban"},
        "Al Bahia": {"tagline": "Emerging Sea View Community", "icon": "🌅", "type": "Emerging Area"},
    }

    return render_template("housing.html",
                           communities=communities,
                           housing_by_community=housing_by_community,
                           community_info=community_info)


@app.route("/api/housing/filter")
def filter_housing():
    budget = int(request.args.get("budget", 200000))
    family_size = int(request.args.get("family_size", 1))
    community = request.args.get("community", "any")
    property_type = request.args.get("property_type", "any")
    results = get_housing_recommendations(budget, family_size, community, property_type)
    return jsonify(results)


@app.route("/temporary-housing")
def temporary_housing():
    conn = get_db()
    hotels = conn.execute(
        "SELECT * FROM temporary_housing WHERE type = 'Hotel' ORDER BY rating DESC"
    ).fetchall()
    serviced = conn.execute(
        "SELECT * FROM temporary_housing WHERE type = 'Serviced Apartment' ORDER BY rating DESC"
    ).fetchall()
    conn.close()
    return render_template("temporary_housing.html",
                           hotels=[dict(h) for h in hotels],
                           serviced=[dict(s) for s in serviced])


@app.route("/airport", methods=["GET", "POST"])
def airport():
    if request.method == "POST":
        data = request.form
        conn = get_db()
        drivers = ["Mohammed Al Rashidi", "Ahmed Al Mansouri", "Khalid Hassan", "Omar Al Zaabi"]
        vehicles = ["Toyota Land Cruiser (White)", "Lexus LX 570 (Black)", "GMC Yukon (Silver)", "Toyota Camry (White)"]
        driver = random.choice(drivers)
        vehicle = random.choice(vehicles)
        conn.execute("""INSERT INTO airport_pickup
            (passenger_name, flight_number, arrival_date, arrival_time, terminal,
             luggage_count, special_requirements, driver_name, vehicle, status)
            VALUES (?,?,?,?,?,?,?,?,?,'confirmed')""", (
            data.get("passenger_name"), data.get("flight_number"),
            data.get("arrival_date"), data.get("arrival_time"),
            data.get("terminal", "T1"), int(data.get("luggage_count", 1)),
            data.get("special_requirements"), driver, vehicle
        ))
        booking_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()

        pickups = conn.execute(
            "SELECT * FROM airport_pickup ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        conn.close()

        flash(f"Pickup booked! Driver: {driver} | Vehicle: {vehicle} | Booking #{booking_id}", "success")
        return render_template("airport.html",
                               pickups=[dict(p) for p in pickups],
                               new_booking={"id": booking_id, "driver": driver, "vehicle": vehicle})

    conn = get_db()
    pickups = conn.execute(
        "SELECT * FROM airport_pickup ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return render_template("airport.html", pickups=[dict(p) for p in pickups])


@app.route("/citytour", methods=["GET", "POST"])
def citytour():
    conn = get_db()
    tours = conn.execute("SELECT * FROM city_tours ORDER BY duration_days").fetchall()
    attractions = conn.execute(
        "SELECT * FROM attractions ORDER BY rating DESC"
    ).fetchall()
    categories = conn.execute(
        "SELECT DISTINCT category FROM attractions ORDER BY category"
    ).fetchall()
    conn.close()

    selected_tour = None
    if request.method == "POST":
        tour_id = request.form.get("tour_id")
        if tour_id:
            conn = get_db()
            selected_tour = conn.execute(
                "SELECT * FROM city_tours WHERE id = ?", (tour_id,)
            ).fetchone()
            conn.close()
            if selected_tour:
                selected_tour = dict(selected_tour)

    return render_template("citytour.html",
                           tours=[dict(t) for t in tours],
                           attractions=[dict(a) for a in attractions],
                           categories=[r["category"] for r in categories],
                           selected_tour=selected_tour)


@app.route("/api/tour/itinerary/<int:tour_id>")
def generate_itinerary(tour_id):
    conn = get_db()
    tour = conn.execute("SELECT * FROM city_tours WHERE id = ?", (tour_id,)).fetchone()
    if not tour:
        return jsonify({"error": "Tour not found"}), 404

    tour = dict(tour)
    attractions_list = conn.execute(
        "SELECT * FROM attractions ORDER BY RANDOM() LIMIT 15"
    ).fetchall()
    conn.close()

    highlights = [h.strip() for h in tour["highlights"].split(",")]
    itinerary = {}
    all_attractions = [dict(a) for a in attractions_list]

    for day in range(1, tour["duration_days"] + 1):
        day_label = f"Day {day}"
        day_items = []
        slots = [("9:00 AM", "Morning"), ("12:30 PM", "Lunch Break"),
                 ("2:00 PM", "Afternoon"), ("6:00 PM", "Evening")]
        for i, (time, period) in enumerate(slots):
            if i < len(all_attractions):
                attr = all_attractions[(day * 4 + i) % len(all_attractions)]
                day_items.append({
                    "time": time,
                    "period": period,
                    "name": attr["name"],
                    "location": attr["location"],
                    "category": attr["category"],
                    "entry_fee": attr["entry_fee_aed"],
                    "tip": f"Rated {attr['rating']}/5 ★"
                })
        itinerary[day_label] = day_items

    return jsonify({"tour": tour, "itinerary": itinerary})


@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()

    ai_result = None
    selected_user = None

    if request.method == "POST":
        user_id = request.form.get("user_id")
        if user_id:
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            conn.close()
            if user:
                user_dict = dict(user)
                selected_user = user_dict
                housing_recs = get_housing_recommendations(
                    user["budget"], user["family_size"],
                    user["preferred_community"], user["property_type"]
                )
                conn = get_db()
                tours = conn.execute(
                    "SELECT * FROM city_tours ORDER BY duration_days LIMIT 3"
                ).fetchall()
                conn.close()
                ai_result = {
                    "summary": generate_ai_summary(user_dict),
                    "score": generate_ai_relocation_score(user_dict),
                    "housing": housing_recs,
                    "tours": [dict(t) for t in tours],
                }

    return render_template("recommendations.html",
                           users=[dict(u) for u in users],
                           ai_result=ai_result,
                           selected_user=selected_user)


@app.route("/api/quick-recommend", methods=["POST"])
def quick_recommend():
    data = request.json
    budget = int(data.get("budget", 100000))
    family_size = int(data.get("family_size", 2))
    community = data.get("community", "any")
    property_type = data.get("property_type", "any")

    housing = get_housing_recommendations(budget, family_size, community, property_type)
    summary = generate_ai_summary(data)
    score = generate_ai_relocation_score(data)

    return jsonify({
        "housing": housing,
        "summary": summary,
        "score": score
    })


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form
        conn = get_db()
        conn.execute("""INSERT INTO contact_inquiries
            (name, email, phone, subject, message) VALUES (?,?,?,?,?)""", (
            data.get("name"), data.get("email"), data.get("phone"),
            data.get("subject"), data.get("message")
        ))
        conn.commit()
        conn.close()
        flash("Thank you! Your inquiry has been received. Our team will contact you within 24 hours.", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")


@app.route("/api/attractions")
def get_attractions():
    category = request.args.get("category", "all")
    conn = get_db()
    if category == "all":
        rows = conn.execute("SELECT * FROM attractions ORDER BY rating DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM attractions WHERE category = ? ORDER BY rating DESC", (category,)
        ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route("/api/faq")
def faq():
    question = request.args.get("q", "").lower()
    faqs = {
        "visa": "UAE employment visas are typically sponsored by your employer. The process takes 2-4 weeks and includes medical fitness test, Emirates ID application, and residency stamp.",
        "school": "Abu Dhabi has excellent international schools following British, American, IB, and other curricula. Top schools include GEMS World Academy, British School Al Khubairat, and Abu Dhabi Grammar School.",
        "bank": "Opening a UAE bank account requires Emirates ID, passport, visa, salary certificate, and proof of address. Top banks include FAB, Emirates NBD, ADCB, and HSBC.",
        "driving": "GCC residents can convert their home country license. Others need to complete UAE driving lessons. The process takes 1-3 months.",
        "cost": "Abu Dhabi is moderately expensive. Expect AED 50,000-200,000+ annually for housing, plus school fees (AED 30,000-80,000/year), car (AED 800-1,500/month), utilities (AED 600-1,200/month).",
        "safe": "Abu Dhabi is consistently ranked one of the world's safest cities with extremely low crime rates.",
        "weather": "Abu Dhabi has hot summers (May-Sept, 40°C+) and pleasant winters (Oct-April, 20-25°C). AC is essential year-round.",
        "culture": "UAE is an Islamic country. Dress modestly in public, respect prayer times, and avoid public displays of affection. Ramadan has special protocols.",
    }
    for key, answer in faqs.items():
        if key in question:
            return jsonify({"answer": answer, "found": True})
    return jsonify({"answer": "Please contact our concierge team for personalized guidance on this topic. We're available 24/7 to assist with your relocation.", "found": False})


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

init_db()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Relocation & Housing Concierge Agent")
    print("  Abu Dhabi Relocation Platform")
    print("="*60)
    print("  Running at: http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
