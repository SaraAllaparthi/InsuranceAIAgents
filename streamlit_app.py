import os, sys
from dotenv import load_dotenv

# Ensure project root is on sys.path so "app_utils" can be imported
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv()

import streamlit as st
from app_utils.policy_api import validate_policy
from app_utils.image_processing import analyze_damage
from app_utils.weather_api import check_weather
from app_utils.decision_engine import evaluate_claim
from app_utils.payments import issue_refund
from app_utils.db import Session, Claim

# UI improvements
st.set_page_config(page_title="AI Agent for Insurance Claim Processing", layout="wide")
st.title("🤖 AI Agent for Insurance Claim Processing")
st.markdown("Use this intelligent assistant to fast‑track your property insurance claims.")

# Line of Business selector
business_line = st.selectbox(
    "Select Use Case:",
    ["Marine – Rain & Hail", "Marine – Water Ingress", "Specialty – Fire-Damage Advance for SME", "Property Insurance Claim"]
)

if business_line == "Property Insurance Claim":
    with st.form("claim_form", clear_on_submit=True):
        policy_no = st.text_input("Policy Number")
        if st.form_submit_button("Validate Policy"):
            valid = validate_policy(policy_no)
            if not valid:
                st.error("❌ Invalid policy number. Please check and try again.")
            else:
                st.success("✅ Policy validated. You may proceed with claim submission.")

    # Only show claim form once policy is validated
    if validate_policy(policy_no):
        with st.form("claim_details_form", clear_on_submit=True):
            name = st.text_input("Name of claimant")
            email = st.text_input("Email")
            date_of_loss = st.date_input("Date of damage")
            location = st.text_input("Location (city, country)")
            photo = st.file_uploader("Upload damage photo", type=["jpg", "png"] )
            submitted = st.form_submit_button("Submit claim")

        if submitted:
            st.write("Processing your claim...")
            damage_info = analyze_damage(photo)
            st.write(f"**Detected damage**: {damage_info['type']} (est. €{damage_info['estimate']})")
            weather_ok = check_weather(location, date_of_loss, damage_info['type'])
            st.write(f"**Weather corroboration**: {'Yes' if weather_ok else 'No'}")
            approved, notes = evaluate_claim(damage_info, weather_ok)

            session = Session()
            record = Claim(
                policy_no=policy_no, name=name, email=email, date_of_loss=date_of_loss,
                location=location, damage_info=damage_info,
                weather_ok=int(weather_ok), approved=int(approved), notes=notes, refund_tx=None
            )
            session.add(record)
            session.commit()

            if approved:
                tx_id = issue_refund(amount=damage_info['estimate'], claimant_email=email)
                record.refund_tx = tx_id
                session.commit()
                st.success(f"✅ Claim approved! Refund ID: {tx_id}")
            else:
                st.error(f"❌ Claim denied: {notes}")

# Demo examples
st.markdown("---")
st.header("Demo Examples")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Example: Reject Claim")
    st.markdown("- **Policy**: DEMO-INVALID\n- **Damage Photo**: Minor crack (non-weather event)\n- **Result**: Claim denied: No matching weather event found.")
with col2:
    st.subheader("Example: Accept Claim")
    st.markdown("- **Policy**: DEMO-12345\n- **Damage Photo**: Rain damage on roof\n- **Result**: Claim approved! Refund ID: TX-DEMO-0001")
