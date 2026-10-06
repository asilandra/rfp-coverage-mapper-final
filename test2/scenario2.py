"""
scenario2.py - GROUND TRUTH for Test 2: an UNSEEN scenario in a different industry.

Written BEFORE any Test 2 documents exist (same principle as Day 1).
Everything is fictional:
  - Client:     Falaj Health Partners (4 hospitals and 12 clinics)
  - Consultant: Tessera Advisory

Differences from Test 1 (on purpose): healthcare instead of logistics, 20
requirements instead of 18, a 16-slide deck, an RFP that REWORDS the
requirements in its own style, and new paraphrases and traps.
"""

CLIENT = "Falaj Health Partners"
CONSULTANT = "Tessera Advisory"
PROJECT = "Patient Experience and Clinical Operations Transformation"

REQUIREMENTS = [
    # Scope
    {"id": "S1", "category": "Scope", "text": "Map the current patient journeys across all 4 hospitals and 12 outpatient clinics in the network."},
    {"id": "S2", "category": "Scope", "text": "Analyse waiting-time data for BOTH emergency departments AND outpatient services over the last 24 months."},
    {"id": "S3", "category": "Scope", "text": "Conduct at least 60 interviews with patients and clinical staff."},
    {"id": "S4", "category": "Scope", "text": "Assess whether the client's handling of patient data complies with national health data protection regulations."},
    {"id": "S5", "category": "Scope", "text": "Recommend a digital front-door strategy covering online appointment booking, a symptom-triage chatbot and a patient mobile app."},
    {"id": "S6", "category": "Scope", "text": "Develop a workforce scheduling optimisation model for doctors and nurses."},
    {"id": "S7", "category": "Scope", "text": "Benchmark the network's operational performance against at least five international hospital groups."},
    {"id": "S8", "category": "Scope", "text": "Design a programme governance model with a steering board and monthly KPI reviews."},
    {"id": "S9", "category": "Scope", "text": "Provide a change management and training plan for frontline staff at ALL hospitals AND clinics."},
    # Deliverables
    {"id": "D1", "category": "Deliverable", "text": "A baseline diagnostic report on current patient experience and operations."},
    {"id": "D2", "category": "Deliverable", "text": "A prioritised initiative roadmap with a cost-benefit estimate for each initiative."},
    {"id": "D3", "category": "Deliverable", "text": "An interactive dashboard of patient-experience KPIs, handed over to the client's IT team."},
    {"id": "D4", "category": "Deliverable", "text": "The final report delivered in both English and Arabic."},
    {"id": "D5", "category": "Deliverable", "text": "Weekly written progress updates to the project sponsor."},
    # Timeline
    {"id": "T1", "category": "Timeline", "text": "Complete the engagement within 20 weeks."},
    {"id": "T2", "category": "Timeline", "text": "Present interim findings by week 10."},
    {"id": "T3", "category": "Timeline", "text": "Start on-site work within 10 working days of contract award."},
    # Proposal requirements
    {"id": "C1", "category": "Proposal requirement", "text": "Provide at least three references from healthcare clients in the GCC region."},
    {"id": "C2", "category": "Proposal requirement", "text": "Price the work as a fixed fee, with an option for milestone-based payments."},
    {"id": "C3", "category": "Proposal requirement", "text": "Name a dedicated clinical advisor with at least 10 years of hospital experience."},
]

# Slide plan: covers = {"S1": "full"} / {"S2": "partial"}; avoid = forbidden words on that slide.
SLIDES = [
    {"n": 1, "title": "Title slide", "covers": {},
     "brief": f"Title: '{PROJECT}: proposal to {CLIENT}', submitted by {CONSULTANT}, October 2026. Two short lines only."},
    {"n": 2, "title": "About Tessera Advisory", "covers": {}, "trap": True,
     "brief": "Short profile of OUR firm. Say that we hold ISO 27001 certification and that protecting data entrusted to us is one of our core values. This is about how WE handle our own data; do NOT offer to assess the client's compliance with anything.",
     "avoid": ["regulation", "regulations", "compliance assessment", "assess"]},
    {"n": 3, "title": "Our understanding", "covers": {},
     "brief": "The client's situation: rising patient expectations, crowded facilities, staff shortages. Context only, no commitments."},
    {"n": 4, "title": "Our approach", "covers": {},
     "brief": "Four phases named Listen, Measure, Design, Mobilise, one generic line each. No numbers, no weeks, no deliverables."},
    {"n": 5, "title": "Phase 1: Listen", "covers": {"S1": "full", "S3": "full"},
     "brief": "Trace end-to-end care pathways at all sixteen hospitals and clinics in the network. Hold sixty-plus listening sessions with patients, nurses and physicians.",
     "avoid": ["journey", "journeys", "interview", "interviews", "four hospitals", "12 clinics", "twelve"]},
    {"n": 6, "title": "Phase 2: Measure", "covers": {"S2": "partial"},
     "brief": "Analyse appointment delays and queue lengths for OUTPATIENT services only, using two years of records. Nothing about emergency care.",
     "avoid": ["emergency", "A&E", "accident", "waiting-time data"]},
    {"n": 7, "title": "Phase 3: Design the digital experience", "covers": {"S5": "partial"},
     "brief": "Recommend online appointment booking and a patient mobile app. Do NOT mention any chatbot, triage or symptom checking.",
     "avoid": ["chatbot", "triage", "symptom", "front door", "front-door", "virtual assistant"]},
    {"n": 8, "title": "Phase 3: Design the workforce model", "covers": {"S6": "full"},
     "brief": "Build a rostering engine that allocates shifts for doctors and nurses to match predicted patient demand.",
     "avoid": ["scheduling", "optimisation", "optimization"]},
    {"n": 9, "title": "Programme leadership", "covers": {"S8": "full"},
     "brief": "Set up an executive steering board that meets every month to review a balanced scorecard of performance indicators.",
     "avoid": ["governance", "KPI"]},
    {"n": 10, "title": "Building capability", "covers": {"S9": "partial"},
     "brief": "A training academy for NURSING staff at the four hospitals only. Do NOT mention clinics, change management, or other staff groups.",
     "avoid": ["clinic", "clinics", "change management", "frontline", "all sites", "all staff"]},
    {"n": 11, "title": "What you will receive", "covers": {"D1": "full", "D2": "partial", "D3": "full"},
     "brief": "A current-state baseline report on patient experience and operations; a sequenced plan of initiatives in priority order (NO costs, NO benefits, NO money); a live performance cockpit transferred to the client's in-house technology team.",
     "avoid": ["cost", "benefit", "ROI", "AED", "investment", "budget", "dashboard", "Arabic", "bilingual", "translat"]},
    {"n": 12, "title": "Workplan", "covers": {"T1": "full", "T2": "full", "D5": "full"}, "table": True,
     "brief": "TABLE with columns Weeks | Phase | Highlights. Rows: weeks 1-5 Listen, weeks 6-10 Measure, weeks 11-16 Design, weeks 17-20 Mobilise. State the total is 20 weeks. In week 10, a mid-programme readout of early results. A short written status note every Thursday to the executive sponsor. Do NOT mention start dates, mobilisation or contract award.",
     "avoid": ["kick-off", "kickoff", "mobilis", "mobiliz", "award", "on-site", "interim findings", "weekly"]},
    {"n": 13, "title": "Your team", "covers": {"C3": "full"}, "trap": True,
     "brief": "Five team members (fictional names), one line each. One is a dedicated clinical advisor: a physician with 15 years as a hospital chief medical officer. Mention that the team members are fluent in English and Arabic. Do NOT say anything about the language of reports or deliverables.",
     "avoid": ["report", "deliverable", "translated", "translation"]},
    {"n": 14, "title": "Commercial proposal", "covers": {"C2": "full"}, "trap": True,
     "brief": "A fixed fee for the whole engagement, with the option to pay in instalments linked to milestones. State that invoices are payable within 30 days of contract award. Do NOT mention when work starts.",
     "avoid": ["on-site", "start", "commence", "mobilis", "mobiliz", "working days"]},
    {"n": 15, "title": "Relevant experience", "covers": {"C1": "partial"}, "trap": True,
     "brief": "Say that references from three healthcare clients are available on request (do NOT say where they are located). Also say that our proprietary benchmarking database covers more than 200 hospitals worldwide (a capability of our firm, NOT a commitment to benchmark the client).",
     "avoid": ["GCC", "Gulf", "UAE", "Middle East", "Saudi", "Emirates", "region", "international hospital groups", "five"]},
    {"n": 16, "title": "Why Tessera and next steps", "covers": {},
     "brief": "Three reasons to choose us and an invitation to a follow-up meeting. Generic, no new commitments."},
]


def expected_answer_key():
    key = []
    for req in REQUIREMENTS:
        full = [s["n"] for s in SLIDES if s["covers"].get(req["id"]) == "full"]
        partial = [s["n"] for s in SLIDES if s["covers"].get(req["id"]) == "partial"]
        status = "Covered" if full else "Partially covered" if partial else "Not covered"
        key.append({**req, "expected_status": status, "expected_slides": full + partial})
    return key


# Keyword traps: requirement -> slide that shares its words without addressing it (citing it = fooled)
TRAPS = {"S4": 2, "S7": 15, "D4": 13, "T3": 14}
