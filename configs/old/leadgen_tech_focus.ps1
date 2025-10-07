[filters]
# --- Core tech focus ---
keywords = cybersecurity, zero trust, analytics, data integration

# --- AI/ML & emerging tech ---
# keywords = AI, ML, artificial intelligence, machine learning, deep learning, natural language processing

# --- Healthcare IT ---
# keywords = EHR, HIPAA, healthcare IT, electronic health record, health informatics

# --- Cloud & security ---
# keywords = cloud, endpoint, encryption, compliance, modernization, FedRAMP

# --- Networking & infrastructure ---
# keywords = SDN, 5G, IoT, edge, broadband

# --- Government buzzwords (toggle cautiously) ---
# keywords = digital transformation, modernization, resilience, innovation

# You can uncomment multiple lines — all keywords are merged.
# Lines beginning with '#' are ignored.

naics_allow = 541511,541512,541513,541519
set_aside_allow = none,small_business,sdb
min_est_value = 50000
agencies_priority = DHS, DOJ, HHS, VA
vehicles_priority = SEWP, CIO-SP3, GWAC

[scoring]
weights = naics:3, set_aside:3, vehicle:2, keywords:3, agency:2, value:2, time:2, history:2
due_soon_days = 14
