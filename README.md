# Relocation & Housing Concierge Agent
## Abu Dhabi Relocation Platform

A complete AI-powered Relocation, City Tour, and Housing Overview Platform for Abu Dhabi, UAE.

---

## Features

- **Relocation Planner** — Create profiles, generate 28-task checklists, AI summaries, and readiness scores
- **Housing Overview** — Browse 24 properties across 14 communities with comparison and filters
- **Temporary Housing** — Hotels and serviced apartments with nightly/monthly cost breakdown
- **Airport Pickup** — Booking management with driver assignment and arrival checklists
- **City Tour Planner** — 8 tour packages with AI-generated day-by-day itineraries
- **AI Recommendations** — Personalized housing and relocation guidance based on your profile
- **FAQ Assistant** — Instant answers on visa, schools, banks, driving, and costs
- **Contact Support** — Inquiry form with subject routing

---

## Quick Start (VS Code / Local)

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Installation

**Step 1 — Open terminal in VS Code** (`Ctrl + `` ` ``)

**Step 2 — Create a virtual environment:**
```bash
python -m venv venv
```

**Step 3 — Activate the virtual environment:**

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

**Step 4 — Install dependencies:**
```bash
pip install flask
```

**Step 5 — Run the application:**
```bash
python app.py
```

**Step 6 — Open your browser:**
```
http://127.0.0.1:5000
```

The database is created automatically on first run with all sample data seeded.

---

## Project Structure

```
relocation-concierge/
│
├── app.py                      # Main Flask application
│
├── templates/
│   ├── base.html               # Shared layout, navbar, footer
│   ├── index.html              # Home page
│   ├── relocation.html         # Relocation profile form
│   ├── relocation_profile.html # Profile view + checklist + AI summary
│   ├── housing.html            # Housing overview + community browser
│   ├── temporary_housing.html  # Hotels & serviced apartments
│   ├── airport.html            # Airport pickup booking
│   ├── citytour.html           # City tour planner + attractions
│   ├── recommendations.html    # AI recommendations engine
│   └── contact.html            # Contact form + FAQ
│
├── static/
│   ├── css/style.css           # Abu Dhabi luxury theme
│   ├── js/main.js              # Interactive features
│   └── images/                 # (Add property/community images here)
│
├── database/
│   └── relocation.db           # SQLite database (auto-created)
│
├── data/
│   ├── housing_data.csv        # 24 property listings
│   ├── attractions.csv         # 20 Abu Dhabi attractions
│   └── communities.csv         # 14 community profiles
│
├── README.md
└── workflow.md
```

---

## Pages & Routes

| URL | Page | Description |
|-----|------|-------------|
| `/` | Home | Overview, stats, services, attractions preview |
| `/relocation` | Relocation Planner | Profile creation form |
| `/relocation/profile/<id>` | My Plan | Checklist + AI summary + housing recs |
| `/housing` | Housing Overview | Community browser + filter + comparison |
| `/temporary-housing` | Temp Housing | Hotels and serviced apartments |
| `/airport` | Airport Pickup | Booking form + arrival management |
| `/citytour` | City Tour Planner | Tours + itinerary generator + attractions |
| `/recommendations` | AI Recommendations | Profile-based + quick AI recommendations |
| `/contact` | Contact Support | Inquiry form + FAQ |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/checklist/update` | POST | Toggle checklist item status |
| `/api/housing/filter` | GET | Filter properties by budget/type/community |
| `/api/tour/itinerary/<id>` | GET | Generate day-by-day tour itinerary |
| `/api/quick-recommend` | POST | Quick AI housing + relocation recommendations |
| `/api/attractions` | GET | Get attractions (optionally filtered by category) |
| `/api/faq` | GET | FAQ assistant — answers common relocation questions |

---

## Database Tables

- **users** — Relocation profiles
- **relocation_checklists** — Checklist tasks linked to users
- **housing_options** — 24 Abu Dhabi property listings
- **temporary_housing** — Hotels and serviced apartments
- **airport_pickup** — Pickup booking records
- **city_tours** — 8 tour packages
- **attractions** — 20 Abu Dhabi attractions
- **contact_inquiries** — Contact form submissions

---

## Future API Integrations

The following integration points are placeholder-ready:

| Integration | Location in Code | Description |
|-------------|-----------------|-------------|
| **Bayut API** | `get_housing_recommendations()` | Live Abu Dhabi property listings |
| **Property Finder API** | `get_housing_recommendations()` | Real-time rental market data |
| **Abu Dhabi Municipality Rental Index** | `housing_options` seeding | Official rent reference data |
| **Google Maps API** | `citytour.html` | Interactive community and attraction maps |
| **OpenAI / Claude AI** | `generate_ai_summary()` | LLM-powered personalized summaries |
| **Airport Transfer Providers** | `airport.html` form | Real booking with dispatch APIs |
| **Hotel Booking Systems** | `temporary_housing.html` | Live availability and booking |
| **UAE TAMM (Ejari)** | Checklist links | Direct government portal links |

---

## Customization

### Add new housing listings
Edit `data/housing_data.csv` and re-seed the database, or add records directly via the `housing_options` table.

### Add new attractions
Edit `data/attractions.csv` and update the `attractions` table.

### Change the AI summary logic
Edit the `generate_ai_summary()` function in `app.py` to integrate with OpenAI or Claude API.

### Add real AI (Claude API example)
```python
import anthropic

def generate_ai_summary(user_data):
    client = anthropic.Anthropic(api_key="YOUR_API_KEY")
    prompt = f"Generate a relocation summary for: {user_data}"
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text
```

---

## Tech Stack

- **Backend:** Python Flask
- **Database:** SQLite (via Python sqlite3)
- **Frontend:** HTML5, CSS3 (custom luxury theme), Vanilla JavaScript
- **Fonts:** Inter (Google Fonts)
- **Design:** Abu Dhabi gold & navy luxury theme, mobile-responsive

---

## Author

Built for Abu Dhabi relocation professionals, HR teams, and expatriate service providers.
