"""
scenario.py - the GROUND TRUTH for our synthetic test.

Key idea: we write the answer key FIRST, then ask Gemini to write documents
that follow it. So we know exactly which requirement each slide covers,
which ones are only partly covered, and which are deliberately missing.

All companies here are fictional:
  - Client:     Qamar Logistics Group (Dubai)
  - Consultant: Meridian Advisory (fictional, so we never put made-up claims under a real firm's name)
"""

CLIENT = "Qamar Logistics Group"
CONSULTANT = "Meridian Advisory"
PROJECT = "AI Transformation Strategy & Roadmap"

# ---------------------------------------------------------------------------
# 1. What the RFP asks for (18 requirements across 4 categories)
# ---------------------------------------------------------------------------
REQUIREMENTS = [
    # Scope of work
    {"id": "S1", "category": "Scope", "text": "Assess the current AI and analytics maturity of all five business units (Ports, Freight, Warehousing, Customs Brokerage, Corporate Services)."},
    {"id": "S2", "category": "Scope", "text": "Identify at least 20 AI use cases and prioritise them by business value and feasibility, with an estimated financial impact for each."},
    {"id": "S3", "category": "Scope", "text": "Assess the readiness of the group's data infrastructure AND its data governance (data ownership, data quality standards and data policies)."},
    {"id": "S4", "category": "Scope", "text": "Benchmark the group's AI maturity against at least three regional and global logistics peers."},
    {"id": "S5", "category": "Scope", "text": "Design an AI target operating model, including an AI Centre of Excellence, key roles and decision rights."},
    {"id": "S6", "category": "Scope", "text": "Develop a Responsible AI framework aligned with the UAE's national AI ethics principles."},
    {"id": "S7", "category": "Scope", "text": "Design a change management and AI upskilling programme reaching approximately 500 employees."},
    {"id": "S8", "category": "Scope", "text": "Deliver two proof-of-concept pilots for top-priority use cases."},
    # Deliverables
    {"id": "D1", "category": "Deliverable", "text": "A current-state assessment report."},
    {"id": "D2", "category": "Deliverable", "text": "A prioritised AI use-case portfolio."},
    {"id": "D3", "category": "Deliverable", "text": "A three-year AI roadmap including investment estimates by year."},
    {"id": "D4", "category": "Deliverable", "text": "A final presentation to the Executive Board."},
    {"id": "D5", "category": "Deliverable", "text": "All final deliverables provided in both Arabic and English."},
    # Timeline
    {"id": "T1", "category": "Timeline", "text": "Complete the full engagement within 16 weeks."},
    {"id": "T2", "category": "Timeline", "text": "Hold an interim Steering Committee review at week 8."},
    {"id": "T3", "category": "Timeline", "text": "Mobilise the team and hold the project kick-off within two weeks of contract signature."},
    # Proposal requirements
    {"id": "C1", "category": "Proposal requirement", "text": "Provide CVs of the proposed team, including at least two Arabic-speaking consultants."},
    {"id": "C2", "category": "Proposal requirement", "text": "Provide fixed-fee pricing broken down by project phase."},
]

# ---------------------------------------------------------------------------
# 2. The deck plan: what each slide must (and must NOT) say
#    covers: {"S1": "full"} or {"S3": "partial"}
#    avoid:  words Gemini must not use on that slide (protects partials/gaps,
#            and forces paraphrasing so keyword matching struggles)
#    trap:   slides that SHARE KEYWORDS with a requirement but don't address it
# ---------------------------------------------------------------------------
SLIDES = [
    {"n": 1, "title": "Title slide", "covers": {},
     "brief": f"Title slide: '{PROJECT} - Proposal to {CLIENT}', submitted by {CONSULTANT}, October 2026. Subtitle only, max 2 short lines."},

    {"n": 2, "title": "About Meridian Advisory", "covers": {}, "trap": True,
     "brief": "Short firm profile and our values. Mention that our values are integrity, ethics and responsible conduct in how WE behave as a firm. Do NOT describe any AI ethics framework or any work for the client."},

    {"n": 3, "title": "Our understanding of your context", "covers": {},
     "brief": "Describe the client's business situation: regional growth, competition from digital-first logistics players, fragmented legacy systems. Describe the context only, NOT the work we will do."},

    {"n": 4, "title": "Our approach at a glance", "covers": {},
     "brief": "Four phases named Diagnose, Discover, Design, Deliver, with one short generic line each. No numbers, no weeks, no deliverable names."},

    {"n": 5, "title": "Phase 1 - Diagnose", "covers": {"S1": "full", "S3": "partial"},
     "brief": "Establish an AI readiness baseline across the five divisions (Ports, Freight, Warehousing, Customs Brokerage, Corporate Services) via interviews and a capability scorecard. Also review the TECHNICAL data platforms: data architecture, cloud infrastructure, system integration. Only the technical side of data.",
     "avoid": ["governance", "ownership", "data quality", "policy", "policies", "maturity"]},

    {"n": 6, "title": "Phase 2 - Discover", "covers": {"S2": "full"},
     "brief": "Build a long-list of 25+ AI opportunities across the business, score each on value vs. ease of implementation, and size each with an indicative EBITDA uplift. Call them 'opportunities' or 'AI plays'.",
     "avoid": ["use case", "use-case"]},

    {"n": 7, "title": "Phase 3 - Design", "covers": {"S5": "full", "D3": "partial"},
     "brief": "Design how AI will be run: an AI hub (centre of excellence), new roles (e.g. AI product owner, ML engineer), and who decides what. Also produce a 3-year sequenced roadmap in waves. The roadmap must NOT mention money in any way.",
     "avoid": ["investment", "budget", "cost", "capex", "AED", "funding", "operating model"]},

    {"n": 8, "title": "Phase 4 - Deliver", "covers": {"S8": "full"},
     "brief": "Build two rapid prototypes (minimum viable products) for the highest-ranked opportunities, tested with real users, with a go/no-go recommendation for scaling.",
     "avoid": ["proof of concept", "proof-of-concept", "pilot", "PoC"]},

    {"n": 9, "title": "Building AI capabilities", "covers": {"S7": "partial"},
     "brief": "Run AI awareness workshops for the senior leadership team only. Do NOT mention change management, staff numbers, or training for the wider workforce.",
     "avoid": ["500", "change management", "all employees", "workforce", "upskilling"]},

    {"n": 10, "title": "What you will receive", "covers": {"D1": "full", "D2": "full", "D4": "full"},
     "brief": "List of deliverables: a baseline diagnostic report on today's position, a ranked opportunity portfolio, and a final session with the Executive Board. Do NOT mention languages.",
     "avoid": ["Arabic", "bilingual", "translation"]},

    {"n": 11, "title": "Workplan", "covers": {"T1": "full", "T2": "full"}, "table": True,
     "brief": "Return a TABLE with columns Weeks | Phase | Key activities. Rows: weeks 1-4 Diagnose, weeks 5-8 Discover, weeks 9-13 Design, weeks 14-16 Deliver. State the total is 16 weeks. Include a mid-point checkpoint with the leadership sponsors in week 8. Do NOT mention kick-off or mobilisation.",
     "avoid": ["kick-off", "kickoff", "mobilis", "mobiliz", "Steering Committee", "contract"]},

    {"n": 12, "title": "Proposed team", "covers": {"C1": "partial"},
     "brief": "Five team members with role and a one-line bio each (fictional names). Note that full CVs are in the appendix. Do NOT mention languages spoken.",
     "avoid": ["Arabic", "language", "bilingual"]},

    {"n": 13, "title": "Commercial proposal", "covers": {"C2": "full"}, "trap": True,
     "brief": "Fixed fee per phase in AED (Diagnose, Discover, Design, Deliver) and the total. Payment milestones: 30% upon contract signature, the rest per phase. Say our fees are benchmarked against market rates.",
     "avoid": ["kick-off", "kickoff", "mobilis", "mobiliz"]},

    {"n": 14, "title": "Relevant experience", "covers": {}, "trap": True,
     "brief": "Three short case studies for OTHER fictional clients: an AI roadmap for a GCC bank, use cases identified for a Saudi retailer, and an Arabic-language chatbot for a government entity. Make clear these were for other clients."},

    {"n": 15, "title": "Why Meridian and next steps", "covers": {},
     "brief": "Three reasons to choose us and a closing line inviting a follow-up meeting. Generic, no new commitments."},
]


def expected_answer_key():
    """Turn the slide plan into the answer key: status + slide numbers per requirement."""
    key = []
    for req in REQUIREMENTS:
        full = [s["n"] for s in SLIDES if s["covers"].get(req["id"]) == "full"]
        partial = [s["n"] for s in SLIDES if s["covers"].get(req["id"]) == "partial"]
        if full:
            status = "Covered"
        elif partial:
            status = "Partially covered"
        else:
            status = "Not covered"
        key.append({**req, "expected_status": status, "expected_slides": full + partial})
    return key
