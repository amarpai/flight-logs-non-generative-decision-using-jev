# Test Jev on pilot tech-log write-ups.
#   Live:    TYPESAFE_API_KEY=... python3 jev_pilot_log_gist.py
#   Offline: python3 jev_pilot_log_gist.py   (uses sample answers)
import json, os, urllib.request

KEY = os.environ.get("TYPESAFE_API_KEY")

# 1. The questions we want answered for every write-up.
QUESTIONS = {
    "system": {"type": "choice", "instructions": "Which aircraft system is affected",
               "criteria": {"cabin": "Seats, galley, lavatory, trim",
                            "hydraulics": "Hydraulic pumps, quantity, pressure",
                            "landing_gear": "Gear, brakes, tyres",
                            "air_conditioning": "Cabin air, smells, temperature"}},
    "affects_safety": {"type": "noul", "instructions": "The defect could affect safe flight"},
}

# 2. Pilot write-ups, with what an engineer said the right answer is.
LOGS = [
    ("Fwd lav faucet drips.",             "cabin",            False),
    ("Hyd sys B qty fluctuating.",        "hydraulics",       True),
    ("#2 main tyre worn to limit.",       "landing_gear",     True),
    ("Burning smell aft cabin in climb.", "air_conditioning", True),
]

# Sample answers so the script runs without a key (not real Jev output).
SAMPLE = {
    "Fwd lav faucet drips.":             ("cabin", .97, .03),
    "Hyd sys B qty fluctuating.":        ("hydraulics", .95, .91),
    "#2 main tyre worn to limit.":       ("landing_gear", .99, .88),
    "Burning smell aft cabin in climb.": ("air_conditioning", .44, .79),
}


def ask_jev(log):
    """Return (system, confidence, safety_probability) for one write-up."""
    if not KEY:
        return SAMPLE[log]
    body = json.dumps({"model": "jev-latest", "state": log, "questions": QUESTIONS}).encode()
    req = urllib.request.Request("https://api.typesafe.ai/v1/systemone", data=body, headers={
        "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req))["answers"]
    return a["system"]["choice"], a["system"]["confidence"], a["affects_safety"]["noul"]


def decide(confidence, safety):
    """3. Plain rules on top of Jev's numbers."""
    if confidence < 0.80:
        return "ENGINEER  (Jev is unsure)"
    if safety > 0.50:
        return "ALERT     (possible safety issue)"
    return "AUTO-FILE (cosmetic)"


# 4. Run the test: is Jev right, and is the routing safe?
correct = 0
for log, expected_system, really_unsafe in LOGS:
    system, confidence, safety = ask_jev(log)
    action = decide(confidence, safety)
    ok = system == expected_system
    correct += ok
    print(f"{'✓' if ok else '✗'} {log:<36} {system:<17} conf {confidence:.2f}  safety {safety:.2f}  → {action}")
    assert not (really_unsafe and action.startswith("AUTO")), f"UNSAFE: auto-filed '{log}'"

print(f"\n{correct}/{len(LOGS)} systems correct · no safety item was auto-filed"
      f" · {'live Jev' if KEY else 'sample answers'}")
