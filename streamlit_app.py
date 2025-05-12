from __future__ import annotations
import os, time, io, random, datetime as dt
from typing import Literal
from uuid import uuid4

import streamlit as st
from pydantic import BaseModel, Field, ValidationError
from PIL import Image

# ────────────────────────────────────────────────────────────────────────────────
# 1️⃣  Mock back‑end helpers   (➡️ swap these for real services as you integrate)
# ────────────────────────────────────────────────────────────────────────────────

def validate_policy(policy_no: str) -> bool:
    """Pretend the policy exists if it starts with "POL" and is 6+ chars."""
    return policy_no.upper().startswith("POL") and len(policy_no) >= 6


def fetch_policy_holder(policy_no: str) -> dict:
    """Return fake customer data."""
    surnames = ["Müller", "Schmidt", "Meier", "Keller"]
    GIVEN = random.choice(["Anna", "Luca", "Sven", "Laura"])
    return {
        "name": f"{GIVEN} {random.choice(surnames)}",
        "email": f"{GIVEN.lower()}@example.com",
        "iban": "CH93‑0076‑2011‑6238‑5295‑7",  # Swiss IBAN mask
    }


def analyze_damage(photo_file: io.BytesIO | None) -> dict:
    """Fake computer‑vision estimate based on file size."""
    if photo_file is None:
        raise ValueError("No photo uploaded")
    size_kb = len(photo_file.getbuffer()) / 1024
    damage_type = "hail" if size_kb % 2 else "wind"
    estimate = round(500 + size_kb * 1.3, 2)
    return {"type": damage_type, "estimate": estimate}


def check_weather(postcode: str, date_of_loss: dt.date, damage_type: str) -> bool:
    """Mock weather API: hail allowed only if date is within last 7 days."""
    days_ago = (dt.date.today() - date_of_loss).days
    if damage_type == "hail":
        return days_ago <= 7
    else:  # wind claims always corroborate for demo simplicity
        return True


def evaluate_claim(damage_info: dict, weather_ok: bool) -> tuple[bool, str]:
    """Simple rules engine.
    Approve if weather corroborates AND estimate ≤ CHF 5 000.
    """
    if not weather_ok:
        return False, "Weather data does not corroborate the reported peril."
    if damage_info["estimate"] > 5000:
        return False, "Damage estimate exceeds instant‑settlement threshold."
    return True, "Approved by rules engine."


def issue_refund(amount: float, iban: str) -> str:
    """Mock payments API → returns a transaction ID."""
    time.sleep(1)  # look realistic 😉
    return f"TX‑{uuid4().hex[:8].upper()}"

# ────────────────────────────────────────────────────────────────────────────────
# 2️⃣  Pydantic schemas  (clean validation + future extensibility)
# ────────────────────────────────────────────────────────────────────────────────

class ClaimInput(BaseModel):
    policy_no: str = Field(..., regex=r"POL\w{3,}")
    date_of_loss: dt.date
    postcode: str = Field(..., min_length=4, max_length=10)
    photo_file: io.BytesIO

# ────────────────────────────────────────────────────────────────────────────────
# 3️⃣  Streamlit UI
# ────────────────────────────────────────────────────────────────────────────────

st.set_page_config("AI Claim Agent", "🛡️", layout="centered")
st.title("🏠 Insurance Claim AI Agent")
st.caption("Demo – instant decisions with transparent behind‑the‑scenes trace")

# --- Sidebar: policy validation -------------------------------------------------
with st.sidebar:
    st.image("https://i.imgur.com/cY9wKOU.png", width=140)
    st.subheader("🔒 Policy Validation")
    policy_no = st.text_input("Policy number", placeholder="POL123456")
    val_btn = st.button("Validate ✨")
    if val_btn:
        is_valid = validate_policy(policy_no)
        if is_valid:
            st.success("Policy validated – continue below.")
            st.session_state["policy_valid"] = True
            st.session_state["policy_no"] = policy_no
        else:
            st.error("Unknown policy number.")
            st.session_state["policy_valid"] = False

# --- Main form ------------------------------------------------------------------
if st.session_state.get("policy_valid"):

    holder = fetch_policy_holder(st.session_state["policy_no"])
    with st.form("claim_form", clear_on_submit=False):
        st.text_input("Policy holder", value=holder["name"], disabled=True)
        st.date_input("Date of loss", key="dol", max_value=dt.date.today())
        st.text_input("Post code", key="postcode")
        photo = st.file_uploader("Upload a damage photo", type=["jpg", "png"], key="photo")
        submit = st.form_submit_button("Submit claim →")

    if submit:
        # Validate input with Pydantic for robustness
        try:
            claim = ClaimInput(
                policy_no=st.session_state["policy_no"],
                date_of_loss=st.session_state["dol"],
                postcode=st.session_state["postcode"],
                photo_file=photo,
            )
        except ValidationError as e:
            st.error("❌ Input validation failed:")
            st.code(e.json(), language="json")
            st.stop()

        # Progress bar & trace log
        progress = st.progress(0, text="Starting claim workflow…")
        trace = st.empty()
        logs: list[str] = []

        def step(label: str, fn, p_idx: int):
            logs.append(label)
            progress.progress(p_idx / 6, text=label)
            trace.code("\n".join(logs))
            result = fn()
            time.sleep(0.6)  # purely cosmetic
            return result

        # --- sequential steps ---------------------------------------------------
        damage = step("Analyzing damage photo…", lambda: analyze_damage(photo), 1)
        weather_ok = step(
            "Checking weather data…",
            lambda: check_weather(claim.postcode, claim.date_of_loss, damage["type"]),
            2,
        )
        approved, reason = step(
            "Running decision engine…",
            lambda: evaluate_claim(damage, weather_ok),
            3,
        )
        progress.progress(1.0, text="Workflow complete.")

        # --- outcome panel -------------------------------------------------------
        st.subheader("Result")
        cols = st.columns(2)
        cols[0].metric("Damage estimate", f"CHF {damage['estimate']:,}")
        cols[1].metric("Weather corroboration", "✅" if weather_ok else "❌")

        if photo:
            st.image(photo, caption="Reported damage", use_column_width=True)

        if approved:
            st.success("✅ Claim approved!")
            st.write(reason)
            # Refund choice
            refund_choice: Literal["default", "new"] = st.radio(
                "Select payout account:",
                ["Use account on record", "Enter a new IBAN"],
                index=0,
            )
            if refund_choice == "Enter a new IBAN":
                new_iban = st.text_input("New IBAN", max_chars=34, placeholder="CH…")
                chosen_iban = new_iban if new_iban else holder["iban"]
            else:
                chosen_iban = holder["iban"]

            if st.button("Process refund 💸"):
                tx_id = issue_refund(damage["estimate"], chosen_iban)
                st.balloons()
                st.success(f"Refund of CHF {damage['estimate']:,} sent. Transaction ID: {tx_id}")
        else:
            st.error("❌ Claim denied.")
            st.write(reason)
            st.info("If you wish to appeal, contact claims@example.com.")

        st.divider()
        with st.expander("🔍 Show behind‑the‑scenes trace"):
            st.code("\n".join(logs))
else:
    st.info("Validate your policy number in the sidebar to begin.")
