"""
ai_claims_demo_app.py ▸ Streamlit front‑end + mock agent logic
13 May 2025 – minor tweak
• Removed leading whitespace before module docstring (fixes IndentationError).
• Logo path constant kept.
"""

from __future__ import annotations
import os, time, random, datetime as dt
from typing import Any
from uuid import uuid4

import streamlit as st
from pydantic import BaseModel, Field, ValidationError

# ────────────────────────────────────────────────────────────────────────────────
# 0️⃣  Branding assets
# ────────────────────────────────────────────────────────────────────────────────
LOGO_PATH = "assets/maverick_logo.png"   # ← place your PNG here

# ────────────────────────────────────────────────────────────────────────────────
# 1️⃣  Mock back‑end helpers   (➡️ swap these for real services as you integrate)
# ────────────────────────────────────────────────────────────────────────────────

def validate_policy(policy_no: str) -> bool:
    return policy_no.upper().startswith("POL") and len(policy_no) >= 6


def fetch_policy_holder(policy_no: str) -> dict[str, str]:
    surnames = ["Müller", "Schmidt", "Meier", "Keller"]
    given = random.choice(["Anna", "Luca", "Sven", "Laura"])
    return {
        "name": f"{given} {random.choice(surnames)}",
        "email": f"{given.lower()}@example.com",
        "iban": "CH93‑0076‑2011‑6238‑5295‑7",
    }


def analyze_damage(photo_bytes: bytes) -> dict[str, Any]:
    if not photo_bytes:
        raise ValueError("No photo uploaded")
    size_kb = len(photo_bytes) / 1024
    damage_type = "hail" if size_kb % 2 else "wind"
    estimate = round(500 + size_kb * 1.3, 2)
    return {"type": damage_type, "estimate": estimate}


def check_weather(postcode: str, date_of_loss: dt.date, damage_type: str) -> bool:
    days_ago = (dt.date.today() - date_of_loss).days
    if damage_type == "hail":
        return days_ago <= 7
    return True


def evaluate_claim(damage_info: dict, weather_ok: bool) -> tuple[bool, str]:
    if not weather_ok:
        return False, "Weather data does not corroborate the reported peril."
    if damage_info["estimate"] > 5_000:
        return False, "Damage estimate exceeds instant‑settlement threshold."
    return True, "Approved by rules engine."


def issue_refund(amount: float, iban: str) -> str:
    time.sleep(1)
    return f"TX‑{uuid4().hex[:8].upper()}"

# ────────────────────────────────────────────────────────────────────────────────
# 2️⃣  Pydantic schema
# ────────────────────────────────────────────────────────────────────────────────

class ClaimInput(BaseModel):
    policy_no: str = Field(..., regex=r"POL\w{3,}")
    date_of_loss: dt.date
    postcode: str = Field(..., min_length=4, max_length=10)
    photo_bytes: bytes

# ────────────────────────────────────────────────────────────────────────────────
# 3️⃣  Streamlit UI
# ────────────────────────────────────────────────────────────────────────────────

st.set_page_config(page_title="Maverick Claims AI", page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🛡️", layout="centered")

# Header with logo
col_logo, col_head = st.columns([1, 3])
with col_logo:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=80)
with col_head:
    st.title("🏠 Insurance Claim AI Agent")
    st.caption("Demo – instant decisions with transparent behind‑the‑scenes trace")

# Sidebar
with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=160)
    else:
        st.markdown("**Maverick AI Group**")
    st.subheader("🔒 Policy Validation")
    policy_no = st.text_input("Policy number", placeholder="POLXXXXX")
    if st.button("Validate ✨"):
        is_valid = validate_policy(policy_no)
        st.session_state["policy_valid"] = is_valid
        st.session_state["policy_no"] = policy_no
        st.success("Policy validated" if is_valid else "Unknown policy number")

# Main flow
if st.session_state.get("policy_valid"):
    holder = fetch_policy_holder(st.session_state["policy_no"])
    with st.form("claim_form"):
        st.text_input("Policy holder", value=holder["name"], disabled=True)
        dol = st.date_input("Date of loss", max_value=dt.date.today())
        postcode = st.text_input("Post code")
        photo = st.file_uploader("Upload a damage photo", type=["jpg", "png"])
        submit = st.form_submit_button("Submit claim →")

    if submit:
        try:
            claim = ClaimInput(
                policy_no=st.session_state["policy_no"],
                date_of_loss=dol,
                postcode=postcode,
                photo_bytes=photo.getvalue() if photo else b"",
            )
        except ValidationError as e:
            st.error("Input validation failed:")
            st.code(e.json())
            st.stop()

        progress = st.progress(0, text="Starting claim workflow…")
        trace = st.empty()
        logs: list[str] = []

        def step(label: str, fn, p_idx: int):
            logs.append(label)
            progress.progress(p_idx / 6, text=label)
            trace.code("\n".join(logs))
            res = fn()
            time.sleep(0.6)
            return res

        damage = step("Analyzing damage photo…", lambda: analyze_damage(claim.photo_bytes), 1)
        weather_ok = step(
            "Checking weather data…",
            lambda: check_weather(claim.postcode, claim.date_of_loss, damage["type"]),
            2,
        )
        approved, reason = step("Running decision engine…", lambda: evaluate_claim(damage, weather_ok), 3)
        progress.progress(1.0, text="Workflow complete.")

        st.subheader("Result")
        cols = st.columns(2)
        cols[0].metric("Damage estimate", f"CHF {damage['estimate']:,}")
        cols[1].metric("Weather corroboration", "✅" if weather_ok else "❌")

        if photo:
            st.image(photo, caption="Reported damage", use_container_width=True)

        if approved:
            st.success("✅ Claim approved!")
            st.write(reason)
            refund_choice = st.radio("Select payout account:", ["Use account on record", "Enter a new IBAN"], index=0)
            chosen_iban = holder["iban"]
            if refund_choice == "Enter a new IBAN":
                new_iban = st.text_input("New IBAN", max_chars=34, placeholder="CH…")
                if new_iban:
                    chosen_iban = new_iban
            if st.button("Process refund 💸"):
                tx_id = issue_refund(damage["estimate"], chosen_iban)
                st.balloons()
                st.success(f"Refund of CHF {damage['estimate']:,} sent. Transaction ID: {tx_id}")
        else:
            st.error("❌ Claim denied.")
            st.write(reason)
            st.info("If you wish to appeal, contact claims@example.com.")

        with st.expander("🔍 Show behind‑the‑scenes trace"):
            st.code("\n".join(logs))
else:
    st.info("Validate your policy number in the sidebar to begin.")
