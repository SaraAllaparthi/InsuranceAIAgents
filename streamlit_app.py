import os, sys
from dotenv import load_dotenv

# Ensure project root is on sys.path so "app_utils" can be imported
# Use absolute path to avoid dirname(__file__) returning empty
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# DEBUG: print to console (view in Streamlit Cloud logs)
print("DEBUG ROOT_DIR:", ROOT_DIR)
print("DEBUG sys.path:", sys.path)
try:
    print("DEBUG root contents:", os.listdir(ROOT_DIR))
    utils_path = os.path.join(ROOT_DIR, 'app_utils')
    print("DEBUG app_utils exists?", os.path.exists(utils_path))
    print("DEBUG app_utils contents:", os.listdir(utils_path))
except Exception as e:
    print("DEBUG error listing directories:", e)

load_dotenv()

import streamlit as st

st.set_page_config(page_title="Insurance Claim AI")
st.title("🏠 Property Insurance Claim")

# Now import utility modules (after sys.path fix)
from app_utils.image_processing import analyze_damage
from app_utils.weather_api import check_weather
from app_utils.decision_engine import evaluate_claim
from app_utils.payments import issue_refund
from app_utils.db import Session, Claim

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
