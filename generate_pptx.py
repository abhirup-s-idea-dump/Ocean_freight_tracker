"""
Script to generate the official 3-Slide Presentation Deck for:
Sustainability Innovation Scholarship by Mr. Nilanjan Mitra Thakur
Ocean Freight Rate & Shipment Tracker (Bluspark OceanOS)
"""

import os
import pptx
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE


def build_deck():
    prs = pptx.Presentation()
    # 16:9 Widescreen standard
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Color Palette Constants
    BG_COLOR = RGBColor(6, 10, 19)         # Deep Navy (#060a13)
    CARD_BG = RGBColor(13, 21, 38)         # Elevated Card (#0d1526)
    CARD_BORDER = RGBColor(24, 40, 77)     # Border (#18284d)
    CYAN_ACCENT = RGBColor(6, 182, 212)    # Electric Cyan (#06b6d4)
    SKY_ACCENT = RGBColor(14, 165, 233)    # Sky Blue (#0ea5e9)
    TEXT_WHITE = RGBColor(248, 250, 252)   # Pure White (#f8fafc)
    TEXT_MUTED = RGBColor(148, 163, 184)   # Slate Muted (#94a3b8)
    TEXT_DIM = RGBColor(100, 116, 139)     # Dim (#64748b)
    EMERALD = RGBColor(16, 185, 129)       # Emerald (#10b981)
    AMBER = RGBColor(245, 158, 11)         # Amber (#f59e0b)
    ROSE = RGBColor(244, 63, 94)           # Rose (#f43f5e)
    INDIGO = RGBColor(99, 102, 241)        # Indigo (#6366f1)

    def set_slide_background(slide):
        bg_shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), prs.slide_width, prs.slide_height
        )
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = BG_COLOR
        bg_shape.line.fill.background()
        return bg_shape

    def add_header(slide, tag_text, title_text, subtitle_text):
        # Category Tag
        tag_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.45), Inches(8.0), Inches(0.4))
        tf = tag_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag_text.upper()
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = CYAN_ACCENT

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.5), Inches(0.7))
        tf2 = title_box.text_frame
        tf2.word_wrap = True
        p2 = tf2.paragraphs[0]
        p2.text = title_text
        p2.font.name = "Arial"
        p2.font.size = Pt(24)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_WHITE

        # Subtitle
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.35), Inches(11.5), Inches(0.4))
        tf3 = sub_box.text_frame
        tf3.word_wrap = True
        p3 = tf3.paragraphs[0]
        p3.text = subtitle_text
        p3.font.name = "Arial"
        p3.font.size = Pt(12)
        p3.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 1: Problem Overview & Architectural Approach
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    add_header(
        s1,
        "Slide 1 of 3 • Problem Statement & Solution Architecture",
        "Ocean Freight Rate & Shipment Tracker (Bluspark OceanOS)",
        "Sustainability Innovation Scholarship Prototype by Mr. Nilanjan Mitra Thakur • Theme: Digitize • Optimize • Democratize"
    )

    # 3 Column Cards on Slide 1
    col_w = Inches(3.64)
    gap = Inches(0.39)
    top_pos = Inches(1.9)
    card_h = Inches(5.0)

    # Column 1: The Problem Space
    x1 = Inches(0.8)
    card1 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x1, top_pos, col_w, card_h)
    card1.fill.solid()
    card1.fill.fore_color.rgb = CARD_BG
    card1.line.color.rgb = CARD_BORDER
    tf = card1.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.3)
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)

    p = tf.paragraphs[0]
    p.text = "1. THE PROBLEM SPACE"
    p.font.name = "Arial"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = ROSE

    bullets1 = [
        ("Rate Fragmentation", "Shipping tariffs remain locked in disconnected PDFs and spreadsheets. Importers struggle to compare rates and miss optimal carrier contracts."),
        ("Schedule Blindspots", "Delayed vessels go unnoticed until after scheduled ETA, creating warehouse idling and expensive port demurrage penalties."),
        ("Billing Overcharges", "Invoices routinely exceed contracted rates without automated cross-verification before payment release."),
        ("Manual Data Re-Keying", "Operational staff waste hours manually typing email rate sheets and status updates into databases.")
    ]
    for b_title, b_desc in bullets1:
        p_t = tf.add_paragraph()
        p_t.space_before = Pt(10)
        p_t.text = f"• {b_title}"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE

        p_d = tf.add_paragraph()
        p_d.text = b_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = TEXT_MUTED

    # Column 2: Architectural Approach
    x2 = x1 + col_w + gap
    card2 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x2, top_pos, col_w, card_h)
    card2.fill.solid()
    card2.fill.fore_color.rgb = CARD_BG
    card2.line.color.rgb = CARD_BORDER
    tf = card2.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.3)
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)

    p = tf.paragraphs[0]
    p.text = "2. ARCHITECTURAL APPROACH"
    p.font.name = "Arial"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    bullets2 = [
        ("Unified Single-Page App", "FastAPI ASGI backend paired with modern Tailwind CSS glassmorphic reactive frontend for instant zero-lag interaction."),
        ("Dynamic Route Constraint Graph", "Origin selection dynamically filters destination ports to only valid contracted liner lanes, preventing invalid queries."),
        ("Rule-Based Status Telemetry", "Autonomous state machine: checks delivered date, overdue ETAs against reference calendar, and carrier advisories."),
        ("Automated Audit Engine", "Pre-payment reconciliation engine computes discrepancy variances down to the cent in both USD and INR.")
    ]
    for b_title, b_desc in bullets2:
        p_t = tf.add_paragraph()
        p_t.space_before = Pt(10)
        p_t.text = f"• {b_title}"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE

        p_d = tf.add_paragraph()
        p_d.text = b_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = TEXT_MUTED

    # Column 3: The 4 Core Modules
    x3 = x2 + col_w + gap
    card3 = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x3, top_pos, col_w, card_h)
    card3.fill.solid()
    card3.fill.fore_color.rgb = CARD_BG
    card3.line.color.rgb = CARD_BORDER
    tf = card3.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0.3)
    tf.margin_left = Inches(0.3)
    tf.margin_right = Inches(0.3)

    p = tf.paragraphs[0]
    p.text = "3. THE 4 CORE MODULES"
    p.font.name = "Arial"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = EMERALD

    bullets3 = [
        ("Module 1: Rate Search", "Instantly compare carriers across routes & 20ft/40ft containers; highlights cheapest carrier and calculates potential savings."),
        ("Module 2: Shipment Tracker", "Live milestone tracking with computed In Transit, Delivered, and Delayed statuses + one-click Excel/CSV data export."),
        ("Module 3: Invoice Checker", "Verifies billed freight against contracted tariffs; flags OVERCHARGED, CORRECT, or UNDERCHARGED with exact amounts."),
        ("Module 4: Email Ingestion", "Regex NLP parser ingests 14 sample emails, auto-updating tariffs & statuses while quarantining newsletters and OOO messages.")
    ]
    for b_title, b_desc in bullets3:
        p_t = tf.add_paragraph()
        p_t.space_before = Pt(10)
        p_t.text = f"• {b_title}"
        p_t.font.name = "Arial"
        p_t.font.size = Pt(11)
        p_t.font.bold = True
        p_t.font.color.rgb = TEXT_WHITE

        p_d = tf.add_paragraph()
        p_d.text = b_desc
        p_d.font.name = "Arial"
        p_d.font.size = Pt(9.5)
        p_d.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 2: Tech Stack & Engineering Decisions
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(
        s2,
        "Slide 2 of 3 • Tech Stack & Engineering Decisions",
        "Modern Full-Stack Architecture & Security Governance",
        "Zero-bloat, high-performance technology stack designed for enterprise reliability and serverless deployment"
    )

    # 4 Cards Layout on Slide 2
    card2_w = Inches(2.76)
    card2_gap = Inches(0.24)
    x_start = Inches(0.8)

    pillars = [
        {
            "tag": "BACKEND API",
            "title": "FastAPI + Uvicorn",
            "color": CYAN_ACCENT,
            "items": [
                ("Python 3.10 - 3.14", "Native async ASGI architecture with microsecond request latencies."),
                ("Pydantic v2 Schemas", "Strict runtime request/response validation ensuring zero malformed payloads."),
                ("RESTful Modular Design", "Separated domain endpoints for rates, tracking, invoices, emails, and auth."),
                ("Built-in Swagger Docs", "Auto-generated OpenAPI documentation accessible live at /docs.")
            ]
        },
        {
            "tag": "DATABASE & STORAGE",
            "title": "SQLite 3 Relational",
            "color": SKY_ACCENT,
            "items": [
                ("ACID Relational Schema", "Normalized tables: users, carrier_rates, shipments, invoice_audit, email_logs."),
                ("Composite Indexes", "Indexes on (origin_port, destination_port, container_type) for O(1) rate queries."),
                ("Automated CSV Seeding", "Auto-populates 100 carrier rates and 20 sample shipments on initial startup."),
                ("Serverless /tmp Engine", "Auto-detects Vercel environment and routes writes to writable /tmp storage.")
            ]
        },
        {
            "tag": "SECURITY & AUTH",
            "title": "PBKDF2 Cryptography",
            "color": INDIGO,
            "items": [
                ("100,000 Iterations", "Passwords hashed with PBKDF2-HMAC-SHA256 and unique 16-byte random salts."),
                ("Role Governance (RBAC)", "Admin (Director) vs User (Specialist) access levels enforced on mutations."),
                ("Stateless HMAC Tokens", "Tamper-proof signed session tokens with expiration and cookie fallback."),
                ("Credential Storage", "Live registration endpoint stores encrypted credentials directly in DB.")
            ]
        },
        {
            "tag": "FRONTEND & UI",
            "title": "Tailwind + Chart.js",
            "color": EMERALD,
            "items": [
                ("Glassmorphism Dark Theme", "Maritime space-navy palette (#060a13) with translucent blur panels."),
                ("Chart.js Telemetry", "Interactive live doughnut visualization of fleet consignment statuses."),
                ("Dynamic DOM State", "Vanilla ES6+ state management without bulky SPA framework overhead."),
                ("CSV Export Engine", "Real-time streaming export of complete shipment reconciliation records.")
            ]
        }
    ]

    for idx, col in enumerate(pillars):
        cx = x_start + idx * (card2_w + card2_gap)
        cshape = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, cx, top_pos, card2_w, card_h)
        cshape.fill.solid()
        cshape.fill.fore_color.rgb = CARD_BG
        cshape.line.color.rgb = CARD_BORDER

        ctf = cshape.text_frame
        ctf.word_wrap = True
        ctf.margin_top = Inches(0.28)
        ctf.margin_left = Inches(0.22)
        ctf.margin_right = Inches(0.22)

        p = ctf.paragraphs[0]
        p.text = col["tag"]
        p.font.name = "Arial"
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = col["color"]

        p_h = ctf.add_paragraph()
        p_h.text = col["title"]
        p_h.font.name = "Arial"
        p_h.font.size = Pt(13)
        p_h.font.bold = True
        p_h.font.color.rgb = TEXT_WHITE

        for ititle, idesc in col["items"]:
            pt = ctf.add_paragraph()
            pt.space_before = Pt(8)
            pt.text = f"• {ititle}"
            pt.font.name = "Arial"
            pt.font.size = Pt(10)
            pt.font.bold = True
            pt.font.color.rgb = TEXT_WHITE

            pd = ctf.add_paragraph()
            pd.text = idesc
            pd.font.name = "Arial"
            pd.font.size = Pt(8.5)
            pd.font.color.rgb = TEXT_MUTED

    # =========================================================================
    # SLIDE 3: Results, Impact & 3-Minute Demo Walkthrough
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(
        s3,
        "Slide 3 of 3 • Implementation Results & Demo Walkthrough",
        "Delivered Outcomes, Audit Results & Sustainability Impact",
        "Evaluated on 100 benchmark rates, 20 live shipments, and 14 autonomous dispatch emails"
    )

    # Top Half: 3 Metric Result Cards
    m_w = Inches(3.64)
    m_gap = Inches(0.39)
    m_h = Inches(2.2)
    m_top = Inches(1.9)

    metrics = [
        ("BILLING LEAKAGE RECOVERED", "$745.00 USD", "₹62,207.50 INR audited across 20 shipments. 3 overcharged carrier invoices instantly caught.", ROSE),
        ("EMAIL PARSING EFFICIENCY", "100% Ingestion", "14 plain-text emails: 5 rate tariffs updated, 5 shipment statuses synced, 4 noise emails filtered.", CYAN_ACCENT),
        ("FLEET ON-WATER VISIBILITY", "20 Active Consignments", "11 In Transit, 6 Port Discharged, 3 Delayed alerts dynamically monitored with zero lag.", EMERALD)
    ]

    for idx, (m_tag, m_val, m_sub, m_col) in enumerate(metrics):
        mx = Inches(0.8) + idx * (m_w + m_gap)
        mcard = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, mx, m_top, m_w, m_h)
        mcard.fill.solid()
        mcard.fill.fore_color.rgb = CARD_BG
        mcard.line.color.rgb = CARD_BORDER

        mtf = mcard.text_frame
        mtf.word_wrap = True
        mtf.margin_top = Inches(0.25)
        mtf.margin_left = Inches(0.25)
        mtf.margin_right = Inches(0.25)

        p = mtf.paragraphs[0]
        p.text = m_tag
        p.font.name = "Arial"
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = m_col

        p2 = mtf.add_paragraph()
        p2.space_before = Pt(4)
        p2.text = m_val
        p2.font.name = "Arial"
        p2.font.size = Pt(22)
        p2.font.bold = True
        p2.font.color.rgb = TEXT_WHITE

        p3 = mtf.add_paragraph()
        p3.space_before = Pt(4)
        p3.text = m_sub
        p3.font.name = "Arial"
        p3.font.size = Pt(9.5)
        p3.font.color.rgb = TEXT_MUTED

    # Bottom Half: 3-Minute Demo Step-by-Step Box
    b_top = Inches(4.35)
    b_w = Inches(11.73)
    b_h = Inches(2.55)

    bcard = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), b_top, b_w, b_h)
    bcard.fill.solid()
    bcard.fill.fore_color.rgb = CARD_BG
    bcard.line.color.rgb = CARD_BORDER

    btf = bcard.text_frame
    btf.word_wrap = True
    btf.margin_top = Inches(0.25)
    btf.margin_left = Inches(0.3)
    btf.margin_right = Inches(0.3)

    bp = btf.paragraphs[0]
    bp.text = "OFFICIAL 3-MINUTE DEMO SCRIPT & EVALUATION ROADMAP"
    bp.font.name = "Arial"
    bp.font.size = Pt(12)
    bp.font.bold = True
    bp.font.color.rgb = SKY_ACCENT

    demo_steps = [
        ("Minute 1: Authentication & Rate Procurement", "Log in via cryptographic portal (Admin/User). Navigate to Tariff Search, select Nhava Sheva ➔ Los Angeles (20ft). Show dynamic destination filtering, cheapest carrier highlight ($2,040 BlueWave), and instant USD/INR cost savings benchmark."),
        ("Minute 2: Fleet Milestones & Invoice Audit", "Open Fleet Tracker: show live doughnut status chart (11 In Transit, 6 Delivered, 3 Delayed). Filter by carrier or Delayed status. Open Invoice Checker: audit SHP1001, proving automated detection of $745 total overcharges."),
        ("Minute 3: Autonomous Email Ingestion & Sustainability", "Trigger Batch Dispatch Ingestion: parse 14 unformatted emails. Show 5 rate tariff updates, 5 shipment alerts, and 4 filtered newsletters without crash. Test custom email in sandbox. Explain sustainability impact: eliminating demurrage fuel waste.")
    ]

    for s_title, s_desc in demo_steps:
        p_st = btf.add_paragraph()
        p_st.space_before = Pt(6)
        p_st.text = f"▶ {s_title}"
        p_st.font.name = "Arial"
        p_st.font.size = Pt(10.5)
        p_st.font.bold = True
        p_st.font.color.rgb = TEXT_WHITE

        p_sd = btf.add_paragraph()
        p_sd.text = s_desc
        p_sd.font.name = "Arial"
        p_sd.font.size = Pt(9.5)
        p_sd.font.color.rgb = TEXT_MUTED

    # Save to multiple convenient destinations
    output_dirs = [
        os.path.join(os.path.dirname(__file__), "presentation"),
        os.path.dirname(__file__),
        r"D:\Local Disk(D)\College\Scholarships\JGECAA\Sustainability Innovation Scholarship by Mr. Nilanjan Mitra Thakur"
    ]

    saved_paths = []
    for d in output_dirs:
        if os.path.exists(d):
            out_file = os.path.join(d, "Ocean_Freight_Tracker_Presentation.pptx")
            prs.save(out_file)
            saved_paths.append(out_file)
            print(f"[OK] Saved presentation to: {out_file}")

    return saved_paths


if __name__ == "__main__":
    paths = build_deck()
    print("Presentation deck generation complete!")
