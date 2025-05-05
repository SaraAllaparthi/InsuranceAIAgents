import os
import sys
from dotenv import load_dotenv

# Ensure project root is on sys.path so "app_utils" can be imported
ROOT_DIR = os.path.dirname(__file__)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

load_dotenv()

# DEBUG: show file structure to diagnose import issues
import os, sys
print("PYTHON SYSPATH:", sys.path)
print("PROJECT ROOT CONTENTS:", os.listdir(os.path.dirname(__file__)))
try:
    print("app_utils contents:", os.listdir(os.path.join(os.path.dirname(__file__), 'app_utils')))
except Exception as e:
    print("Could not list app_utils/:", e)


import streamlit as st

# DEBUG: show environment for imports
st.write("**Debug: sys.path**", sys.path)
try:
    st.write("**Debug: root contents**", os.listdir(os.path.dirname(__file__)))
    st.write("**Debug: app_utils contents**", os.listdir(os.path.join(os.path.dirname(__file__), 'app_utils')))
except Exception as e:
    st.write("Debug error listing directories:", e)

# Now import utility modules
from app_utils.image_processing import analyze_damage
from app_utils.weather_api import check_weather
from app_utils.decision_engine import evaluate_claim
from app_utils.payments import issue_refund
from app_utils.db import Session, Claim

st.set_page_config(page_title="Insurance Claim AI")
st.title("🏠 Property Insurance Claim")

with st.form("claim_form", clear_on_submit=True):
    name = st.text_input("Name of claimant")
    email = st.text_input("Email")
    date_of_loss = st.date_input("Date of damage")
    location = st.text_input("Location (city, country)")
    photo = st.file_uploader("Upload damage photo", type=["jpg", "png"])
    submitted = st.form_submit_button("Submit claim")

if submitted:
    st.write("Processing your claim...")

    # 1) Damage detection
    damage_info = analyze_damage(photo)
    st.write(f"Damage: {damage_info['type']}, estimate: €{damage_info['estimate']}")

    # 2) Weather verification
    weather_ok = check_weather(location, date_of_loss, damage_info['type'])
    st.write(f"Weather match: {'Yes' if weather_ok else 'No'}")

    # 3) Decision
    approved, notes = evaluate_claim(damage_info, weather_ok)

    # 4) Persist audit log
    session = Session()
    record = Claim(
        name=name,
        email=email,
        date_of_loss=date_of_loss,
        location=location,
        damage_info=damage_info,
        weather_ok=int(weather_ok),
        approved=int(approved),
        notes=notes,
        refund_tx=None
    )
    session.add(record)
    session.commit()

    if approved:
        # 5) Issue refund
        tx_id = issue_refund(amount=damage_info['estimate'], claimant_email=email)
        record.refund_tx = tx_id
        session.commit()
        st.success(f"✅ Claim approved! Refund ID: {tx_id}")
    else:
        st.error(f"❌ Claim denied: {notes}")
