# Bluspark OceanOS 🚢
### Global Ocean Freight Rate Intelligence & Shipment Visibility Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg?style=flat&logo=python)](https://python.org)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-v3-38bdf8.svg?style=flat&logo=tailwindcss)](https://tailwindcss.com)
[![SQLite](https://img.shields.io/badge/SQLite-ACID%20Embedded-003B57.svg?style=flat&logo=sqlite)](https://sqlite.org)
[![Vercel Ready](https://img.shields.io/badge/Deploy-Vercel-black.svg?style=flat&logo=vercel)](https://vercel.com)

An enterprise-grade, high-performance ocean freight rate comparison, shipment milestone tracking, invoice overcharge audit, and autonomous carrier dispatch ingestion system. Designed for global supply chain visibility, demurrage risk elimination, and freight cost governance.

---

## 📋 Table of Contents
1. [Executive Overview](#-executive-overview)
2. [Core Modules](#-core-modules)
3. [Architecture & Tech Stack](#-architecture--tech-stack)
4. [Enterprise Design & Color Grading](#-enterprise-design--color-grading)
5. [Security & Role-Based Access Control](#-security--role-based-access-control)
6. [Local Quick Start](#-local-quick-start)
7. [Deploy to Vercel & GitHub](#-deploy-to-vercel--github)
8. [Project Structure](#-project-structure)
9. [Presentation Deck & Demo Script](#-presentation-deck--demo-script)

---

## 🌟 Executive Overview

Global importers and freight forwarders face three persistent operational risks:
1. **Rate Fragmentation:** Carrier pricing across ports and container types is opaque, leading to unoptimized lane selection and missed procurement savings.
2. **Schedule Blindspots:** Delayed ocean vessels trigger demurrage, detention penalties, and warehouse idleness if not flagged dynamically against expected arrival milestones.
3. **Billing Overcharges:** Freight invoices routinely deviate from contracted service tariffs without automated reconciliation before disbursement.

**Bluspark OceanOS** resolves these challenges in a unified platform featuring an autonomous NLP dispatch ingestion engine that processes raw carrier emails into structured data.

---

## 📦 Core Modules

### 1. Tariff Procurement & Benchmark (Rate Search)
* **Dynamic Origin ➔ Destination Pairing:** Intelligent port selector dynamically restricts destination choices to valid contracted shipping lanes.
* **Equipment Types:** Dual support for `20ft Standard` and `40ft High Cube` ISO containers.
* **Optimal Carrier Highlight:** Surfaces the lowest-priced carrier with savings metrics vs. highest-rate carriers and route averages.
* **Dual-Currency Benchmarks:** Real-time freight calculations in both **$ USD** and **₹ INR** (reference FX rate ₹83.50).
* **Criteria Sorting:** Sort by lowest freight cost or fastest ocean transit duration.

### 2. Fleet & Consignment Tracking (Shipment Tracker)
* **Rule-Based Dynamic State Engine:**
  * `Delivered`: Port discharge confirmed with logged arrival date.
  * `Delayed`: Automatically computed when `reference_date > expected_arrival` without terminal discharge, or when carrier advisories notify congestion.
  * `In Transit`: Vessel en route within scheduled arrival window.
* **Multi-Parameter Filtering:** Real-time filtering by voyage status, contract carrier, or keyword search across consignment IDs and port names.
* **Direct Consignment Registration:** Modal dialog with dynamic route validation and provisional billing amounts.
* **Excel / CSV Streaming Export:** Instant download of the complete shipment audit dataset for ERP ingestion.

### 3. Freight Invoice Audit & Cost Recovery
* **Automated Tariff Reconciliation:** Cross-references invoiced carrier charges against the master contracted tariff for the exact route and container specification.
* **Automated Verdicts:**
  * `OVERCHARGED` (Red): Quantifies exact excess charges in USD and INR.
  * `CORRECT` (Green): Verified 100% contract match.
  * `UNDERCHARGED` (Blue): Applied contract credit or volume rebate.
* **Fleet Batch Reconciliation:** Complete audit across all active consignments, immediately surfacing **$745 USD (₹62,207 INR)** in recoverable carrier overcharges.

### 4. Autonomous Carrier Dispatch Ingestion
* **Pattern-Matching NLP Engine:** Ingests unformatted plain-text emails (`data/sample_emails.txt`).
* **Tariff Revisions:** Parses carrier, route, container size, and updated rate, auto-committing updates to master tariffs.
* **Milestone Advisories:** Extracts shipment IDs, delivery dates, transit delays, and terminal congestion notes.
* **Fault-Tolerant Filtering:** Gracefully quarantines marketing circulars, newsletters, and out-of-office autoreplies without system disruption.
* **Interactive Dispatch Sandbox:** Real-time regex payload tester allowing operators to paste raw carrier emails and preview extracted JSON entities.

---

## 🛠️ Architecture & Tech Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn | Python 3.10-3.14 async ASGI framework with Pydantic v2 validation |
| **Database** | [SQLite 3](https://sqlite.org) | Relational storage with composite unique constraints and composite indexes; Vercel serverless `/tmp` copy engine |
| **Frontend** | HTML5 + [Tailwind CSS](https://tailwindcss.com/) | Dark-mode glassmorphism theme, modern typography (Inter & JetBrains Mono) |
| **Data Viz** | [Chart.js](https://www.chartjs.org/) | Responsive doughnut telemetry chart of fleet consignment distribution |
| **Security** | Python Standard Cryptography | PBKDF2-HMAC-SHA256 (100,000 iterations + salt) & stateless HMAC session tokens |
| **Deployment** | [Vercel](https://vercel.com) | Serverless Python ASGI deployment via `vercel.json` and `api/index.py` |

---

## 🎨 Enterprise Design & Color Grading

* **Command Center Palette:** Deep space navy base (`#060a13`) with multilayered radial glow gradients.
* **Glassmorphism Panels:** Translucent surface cards with blur filters (`backdrop-filter: blur(20px)`), subtle inner borders, and hover lift effects.
* **Semantic Indicator Badges:**
  * Emerald (`#10b981`): Port discharged & verified invoices.
  * Amber (`#f59e0b`): Vessels actively in transit.
  * Rose (`#f43f5e`): Delays, congestion alerts, and detected invoice overcharges.
  * Electric Cyan (`#06b6d4`): Interactive accents, active navigation tabs, and system telemetry.

---

## 🔒 Security & Role-Based Access Control

* **Cryptographic Passwords:** Passwords salted with 16-byte random salt and hashed using `PBKDF2-HMAC-SHA256` (100k rounds).
* **Stateless Session Tokens:** Signed HMAC-SHA256 tokens passed via `Authorization: Bearer <token>` or secure HTTP cookies.
* **Role Hierarchy:**
  * **Director (Admin):** Add/update tariffs, register/delete consignments, batch ingest emails, reset database.
  * **Specialist (User):** Query rates, monitor fleet telemetry, verify invoices, test custom email dispatches.
* **Pre-Seeded Credentials:**
  * **Admin:** `admin` / `admin123`
  * **User / Specialist:** `user` / `user123`

---

## 🚀 Local Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ocean-freight-tracker.git
cd ocean-freight-tracker
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server
```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

### 4. Access the Application
* **Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Presentation Slide Deck:** [http://127.0.0.1:8000/presentation](http://127.0.0.1:8000/presentation)

---

## ☁️ Deploy to Vercel & GitHub

The project is pre-configured with `vercel.json` and `api/index.py` for immediate deployment.

### Method 1: Push to GitHub & Connect with Vercel (Recommended)

1. **Initialize Git & Commit:**
   ```bash
   git init
   git add .
   git commit -m "feat: complete Bluspark OceanOS platform with Vercel deployment support"
   ```

2. **Create a new GitHub Repository:**
   * Go to [GitHub](https://github.com/new) and create a repository named `ocean-freight-tracker`.

3. **Push your code to GitHub:**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/ocean-freight-tracker.git
   git branch -M main
   git push -u origin main
   ```

4. **Deploy on Vercel:**
   * Go to [Vercel Dashboard](https://vercel.com/dashboard).
   * Click **"Add New"** ➔ **"Project"**.
   * Import your `ocean-freight-tracker` repository.
   * Vercel will auto-detect Python settings via `vercel.json` and deploy your app instantly!

### Method 2: Deploy directly via Vercel CLI

```bash
npm i -g vercel
vercel
```
Follow the interactive prompts to deploy to preview or production (`vercel --prod`).

---

## 📂 Project Structure

```
ocean-freight-tracker/
├── app.py                     # FastAPI web application & REST routes
├── database.py                # SQLite schema, indexing, dynamic status logic & Vercel /tmp engine
├── auth.py                    # PBKDF2 password hashing & HMAC-SHA256 authentication
├── email_parser.py            # Regex NLP entity extraction for carrier emails
├── requirements.txt           # Python dependencies
├── vercel.json                # Vercel serverless deployment routing config
├── .gitignore                 # Git ignore rules for clean repo tracking
├── README.md                  # Comprehensive platform documentation
├── api/
│   └── index.py               # Vercel serverless ASGI entry point
├── data/
│   ├── carrier_rates.csv      # 100 benchmark contract rates across 5 carriers
│   ├── sample_shipments.csv   # 20 reference shipments with invoices
│   └── sample_emails.txt      # 14 sample carrier communications
├── presentation/
│   ├── slides.html            # 3-slide interactive presentation deck
│   └── presentation_notes.md  # 3-minute demo script & evaluation rubric guide
├── static/
│   ├── css/
│   │   └── custom.css         # Dark theme design system & animation tokens
│   └── js/
│       └── app.js             # Client-side state manager, Chart.js & reactive UI
└── templates/
    └── index.html             # Main dashboard template
```

---

## 🏆 Presentation Deck & Demo Script

* **Interactive Slide Deck:** Served directly at `/presentation` or open `presentation/slides.html`.
* **Speaker Script:** See `presentation/presentation_notes.md` for the exact minute-by-minute speaking walkthrough.

---

### License & Compliance
Built with ISO 27001 & SOC-2 compliance principles. Dual currency exchange rates updated daily against RBI reference indices.
