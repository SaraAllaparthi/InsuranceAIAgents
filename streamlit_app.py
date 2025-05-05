import os
import sys
from dotenv import load_dotenv

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Load environment variables
load_dotenv()

import streamlit as st
from PIL import Image
from app_utils.policy_api import validate_policy
from app_utils.image_processing import analyze_damage
from app_utils.weather_api import check_weather
from app_utils.decision_engine import evaluate_claim
from app_utils.payments import issue_refund
from app_utils.db import Session, Claim

# Sidebar logo and policy validation
logo_path = os.path.join(ROOT_DIR, "Logo.png")
if os.path.exists(logo_path):
    img = Image.open(logo_path)
    st.sidebar.image(img, width=150)
else:
    st.sidebar.markdown("**Maverick AI Group**")

st.sidebar.header("🔒 Policy Validation")
policy_no = st.sidebar.text_input("Policy Number")
if st.sidebar.button("Validate Policy"):
    if validate_policy(policy_no):
        st.sidebar.success("✅ Policy validated. You may proceed.")
    else:
        st.sidebar.error("❌ Invalid policy number.")

# Main title and description
st.title("AI Agents for Insurance Claim Processing")
st.markdown("Submit your property insurance claim and get an instant AI-powered decision.")

# Claim form
if validate_policy(policy_no):
    with st.form("claim_form", clear_on_submit=True):
        policy_holder = st.text_input("Name of policy holder")
        email = st.text_input("Email")
        date_of_loss = st.date_input("Date of damage")
        postcode = st.text_input("Postcode")
        photo = st.file_uploader("Upload damage photo", type=["jpg", "png"])
        submitted = st.form_submit_button("Submit claim")

    if submitted:
        with st.spinner("Processing claim..."):
            damage_info = analyze_damage(photo)
            weather_ok = check_weather(postcode, date_of_loss, damage_info["type"])
            approved, notes = evaluate_claim(damage_info, weather_ok)

        # Display results
        col1, col2 = st.columns(2)
        col1.metric("Damage Estimate (€)", damage_info["estimate"])
        col2.metric("Weather Corroboration", "✅" if weather_ok else "❌")

        img_col, info_col = st.columns([1, 2])
        img_col.image(photo, caption="Uploaded Damage", use_container_width=True)
        info_col.write(f"**Decision:** {'Approved' if approved else 'Denied'}")

        # Save to DB
        session = Session()
        record = Claim(
            policy_no=policy_no,
            name=policy_holder,
            email=email,
            date_of_loss=date_of_loss,
            location=postcode,
            damage_info=damage_info,
            weather_ok=int(weather_ok),
            approved=int(approved),
            notes=notes,
            refund_tx=None
        )
        if approved:
            tx_id = issue_refund(amount=damage_info["estimate"], claimant_email=email)
            record.refund_tx = tx_id
            st.success(f"✅ Claim approved! Refund ID: {tx_id}")
        else:
            st.error(f"❌ Claim denied: {notes}")
        session.add(record)
        session.commit()
else:
    st.info("Please validate your policy number in the sidebar to begin your claim.")
