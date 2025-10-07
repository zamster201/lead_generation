[filters]
# Keywords tailored to ClearTrend's tech portfolio (e.g., financial analytics, cloud data)
keywords = market data analytics, investment research tools, financial cloud platform, cybersecurity finance, data visualization, emergent technologies, IT OT integration
# NAICS codes for relevant sectors (e.g., 523210 for securities brokerage; add yours)
naics_codes = 523210, 541511, 541512, 541519, 541618
# Min days to due date for actionable leads
min_days_to_due = 30
# Max opportunities per run
limit = 50
#  Test
[scoring]
# Thresholds (0-100)
fit_threshold = 70
risk_threshold = 50  ; Lower risk score is better
# Weights for fit: keywords (0.6), NAICS (0.4)
keyword_weight = 0.6
naics_weight = 0.4