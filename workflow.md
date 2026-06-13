# Application Workflow — Relocation & Housing Concierge

## Overview

This document explains how data flows through the Relocation & Housing Concierge platform — from the moment a user lands on the home page through to receiving a personalized AI relocation roadmap.

---

## User Journey Flow

```
HOME PAGE
   │
   ├──> RELOCATION PLANNER (Create Profile)
   │       │
   │       └──> PROFILE PAGE (AI Summary + Checklist + Housing Recs)
   │
   ├──> HOUSING OVERVIEW (Browse Communities & Properties)
   │       │
   │       └──> AI RECOMMENDATIONS (Personalized Match)
   │
   ├──> TEMPORARY HOUSING (Hotels & Serviced Apartments)
   │
   ├──> AIRPORT PICKUP (Book Transfer)
   │
   ├──> CITY TOUR PLANNER (Choose Tour + Generate Itinerary)
   │       │
   │       └──> FAQ ASSISTANT (Ask Relocation Questions)
   │
   └──> CONTACT SUPPORT (Inquiry Form)
```

---

## Step-by-Step Application Flow

### Step 1 — User Creates Relocation Profile

**Page:** `/relocation`

User fills in:
- Name, email, nationality
- Family size (1–6+)
- Annual housing budget (slider: AED 40,000 – 350,000)
- Preferred community (14 options or "No Preference")
- Property type (Apartment / Villa / Any)
- Move date
- Employer / company

**On submit:**
- Flask `POST /relocation` route receives form data
- Inserts record into `users` table
- Calls `generate_checklist_tasks(user_id)` — creates 28 tasks across 3 categories
- Redirects to `/relocation/profile/<user_id>`

---

### Step 2 — Profile Page Generated

**Page:** `/relocation/profile/<id>`

Flask queries:
1. `users` table — user profile data
2. `relocation_checklists` WHERE user_id — all 28 tasks grouped by category
3. `get_housing_recommendations()` — top 3 property matches
4. `generate_ai_summary()` — personalized AI text summary
5. `generate_ai_relocation_score()` — score 0–100

Page renders:
- Readiness score with animated gauge
- Profile summary cards (7 data points)
- Checklist (clickable, updates via `/api/checklist/update`)
- AI concierge summary with markdown formatting
- Top 3 recommended properties

---

### Step 3 — Housing Overview

**Page:** `/housing`

Flask queries:
- All housing options ordered by community
- Distinct community list for tab navigation

Features:
- **Filter Bar** — calls `GET /api/housing/filter?budget=&family_size=&community=&property_type=`
- Returns matching properties as JSON → rendered as property cards by JS
- **Community Tabs** — all 14 communities with property listings per tab
- **Comparison Table** — budget range, school access, family rating per community

---

### Step 4 — AI Recommendations

**Page:** `/recommendations`

Two paths:

**Path A — Profile-based:**
- Dropdown selects saved user profile
- `POST /recommendations` → queries user, runs `get_housing_recommendations()` + `generate_ai_summary()`
- Renders AI summary + property cards + tour suggestions

**Path B — Quick Recommend:**
- Form fills budget, family size, community, type
- `POST /api/quick-recommend` → JSON response
- JS renders score gauge, AI summary (markdown parsed), property cards

---

### Step 5 — City Tour & Itinerary

**Page:** `/citytour`

Static load:
- 8 tour packages from `city_tours` table
- 20 attractions from `attractions` table
- Category list for filter buttons

Dynamic (JavaScript):
- `generateItinerary(tour_id)` → `GET /api/tour/itinerary/<id>`
- Returns tour data + randomized day-by-day schedule
- Rendered as itinerary cards in the output div

FAQ Assistant:
- `askFAQ()` → `GET /api/faq?q=<question>`
- Server-side keyword matching returns relevant answer
- Quick-topic buttons pre-fill the input

---

### Step 6 — Airport Pickup

**Page:** `/airport`

- Form submits `POST /airport`
- Flask randomly assigns driver name and vehicle from predefined lists
- Inserts into `airport_pickup` table with status = "confirmed"
- Flash message shows driver/vehicle assignment
- Booking history table shows recent pickups

---

### Step 7 — Contact & Inquiry

**Page:** `/contact`

- `POST /contact` → inserts into `contact_inquiries` table
- Flash success message confirms receipt
- Static FAQ section addresses 6 common questions

---

## Database Flow Diagram

```
users (1)
  │
  ├──> relocation_checklists (many)
  │       └── user_id FK → users.id
  │
  └──> airport_pickup (many)
          └── user_id FK → users.id

housing_options (independent — queried by filter)
temporary_housing (independent — queried by type)
city_tours (independent — queried by id)
attractions (independent — queried by category)
contact_inquiries (independent — form submissions)
```

---

## AI Logic

### `generate_ai_summary(user_data)` → `str`

Pure Python — no external API required. Logic:
1. Classifies budget as premium / mid-range / budget-friendly
2. Classifies family type (executive couple / family / large family)
3. Selects top 3 community recommendations based on budget tier
4. Generates property strategy recommendation
5. Adds temporary accommodation advice
6. Outputs multi-paragraph formatted markdown text

**To integrate real LLM (Claude/OpenAI):** Replace function body with API call.
See README.md → "Add real AI" section.

### `generate_ai_relocation_score(user_data)` → `int` (0–100)

Scoring rubric:
- Base score: 70
- Budget > AED 100,000: +10
- Family size ≤ 4: +5
- Move date > 60 days away: +15
- Move date 30–60 days: +8
- Cap: 100

---

## Key API Endpoints

| Endpoint | Input | Output | Used By |
|----------|-------|--------|---------|
| `POST /api/checklist/update` | `{id, status}` | `{success}` | Checklist click handler |
| `GET /api/housing/filter` | Query params | `[housing_objects]` | Housing filter bar |
| `GET /api/tour/itinerary/<id>` | tour_id | `{tour, itinerary}` | Tour itinerary generator |
| `POST /api/quick-recommend` | `{budget, family_size, ...}` | `{housing, summary, score}` | Quick recommend form |
| `GET /api/attractions` | `?category=` | `[attraction_objects]` | Attraction grid |
| `GET /api/faq` | `?q=question` | `{answer, found}` | FAQ assistant |

---

## File Responsibility Map

| File | Responsibility |
|------|---------------|
| `app.py` | All routes, database logic, AI generation functions |
| `templates/base.html` | Shared navbar, footer, flash messages, CSS/JS links |
| `templates/index.html` | Home page — stats, services grid, area grid, attractions preview |
| `templates/relocation.html` | Profile creation form with range slider |
| `templates/relocation_profile.html` | Profile display — checklist, score, AI summary, property recs |
| `templates/housing.html` | Community tabs, filter bar, comparison table |
| `templates/temporary_housing.html` | Hotels and serviced apartments tabs |
| `templates/airport.html` | Pickup booking form and history table |
| `templates/citytour.html` | Tour cards, itinerary output, FAQ assistant, attraction grid |
| `templates/recommendations.html` | Profile selector, quick form, AI results display |
| `templates/contact.html` | Contact form, contact cards, FAQ list |
| `static/css/style.css` | Abu Dhabi luxury gold/navy theme, all component styles |
| `static/js/main.js` | Tab system, checklist toggling, API calls, itinerary generation |
| `database/relocation.db` | SQLite database (auto-created) |
| `data/*.csv` | Reference data for housing, attractions, communities |
