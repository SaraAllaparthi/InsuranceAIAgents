### 1. Project Structure
```
insurance_claims_mvp/
├── streamlit_app.py         # Frontend entrypoint
├── utils/
│   ├── __init__.py
│   ├── image_processing.py  # functions to analyze uploaded images
│   ├── weather_api.py        # functions to fetch & parse weather data
│   ├── decision_engine.py    # core rules to validate and approve claims
│   ├── payments.py           # refund integration
│   └── db.py                 # audit log persistence
├── requirements.txt         # pip dependencies
├── Dockerfile               # containerization
├── docker-compose.yml       # compose config
└── README.md                # setup and run instructions
```  

---

### 2. streamlit_app.py
```python
import streamlit as st
from datetime import datetime
from utils.image_processing import analyze_damage
from utils.weather_api import check_weather
from utils.decision_engine import evaluate_claim
from utils.payments import issue_refund
from utils.db import Session, Claim

st.set_page_config(page_title="Insurance Claim AI")

st.title("🏠 Property Insurance Claim")

# 1) Collect form data
with st.form("claim_form", clear_on_submit=True):
    name = st.text_input("Name of claimant")
    email = st.text_input("Email")
    date_of_loss = st.date_input("Date of damage")
    location = st.text_input("Location (city, country)")
    photo = st.file_uploader("Upload damage photo", type=["jpg", "png"])
    submitted = st.form_submit_button("Submit claim")

if submitted:
    st.write("Processing your claim...")
    # 2) Analyze image
    damage_info = analyze_damage(photo)
    # 3) Verify weather
    weather_ok = check_weather(location, date_of_loss, damage_info['type'])
    # 4) Decision
    approved, notes = evaluate_claim(damage_info, weather_ok)

    # 5) Persist audit log
    session = Session()
    record = Claim(
        name=name, email=email, date_of_loss=date_of_loss,
        location=location, damage_info=damage_info,
        weather_ok=int(weather_ok), approved=int(approved),
        notes=notes, refund_tx=None
    )
    session.add(record)
    session.commit()

    if approved:
        # 6) Issue refund
        tx_id = issue_refund(amount=damage_info['estimate'], claimant_email=email)
        # update record
        record.refund_tx = tx_id
        session.commit()
        st.success(f"Claim approved! Refund issued, transaction ID: {tx_id}")
    else:
        st.error(f"Claim denied: {notes}")
```  

---

### 3. utils/image_processing.py
```python
# If you don't have access to a paid model, you can use an open-source checkpoint like YOLOv5
# (https://github.com/ultralytics/yolov5) or Detectron2 Zoo models.
import torch
from PIL import Image
import io

# Download a small YOLOv5s model automatically
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
CATEGORY_MAPPING = {0: 'rain_damage', 1: 'fire_damage', 2: 'other'}

def analyze_damage(uploaded_file):
    img = Image.open(io.BytesIO(uploaded_file.read()))
    results = model(img)
    det = results.xyxy[0]
    if len(det) == 0:
        return {"type": "unknown", "estimate": 0}
    cls = int(det[0, 5])
    damage_type = CATEGORY_MAPPING.get(cls, 'other')
    area = (det[0,2]-det[0,0])*(det[0,3]-det[0,1])
    estimate = max(500, min(5000, int(area/1000)))
    return {"type": damage_type, "estimate": estimate}
```  

---

### 4. utils/weather_api.py
```python
import os, requests

def check_weather(location, date, damage_type):
    key = os.getenv('OWM_API_KEY')
    geo = requests.get(
       f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={key}"
    ).json()[0]
    lat, lon = geo['lat'], geo['lon']
    dt = int(date.strftime('%s'))
    res = requests.get(
      f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&dt={dt}&appid={key}"
    ).json()
    for h in res.get('hourly', []):
        if damage_type == 'rain_damage' and h.get('rain', {}).get('1h', 0) > 0:
            return True
    return False
```  

---

### 5. utils/decision_engine.py
```python
# Simple rule: only approve if weather matches damage type

def evaluate_claim(damage_info, weather_ok):
    if damage_info['type'] == 'rain_damage' and weather_ok:
        return True, ""
    return False, "No matching weather event found"
```  

---

### 6. utils/payments.py
```python
import os, stripe
stripe.api_key = os.getenv('STRIPE_API_KEY')

def issue_refund(amount, claimant_email):
    payment_intent = stripe.PaymentIntent.create(
        amount=int(amount * 100),
        currency='eur',
        receipt_email=claimant_email,
        payment_method_types=['card'],
    )
    refund = stripe.Refund.create(payment_intent=payment_intent.id)
    return refund.id
```  

---

### 7. utils/db.py
```python
from sqlalchemy import create_engine, Column, Integer, String, Date, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///claims.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class Claim(Base):
    __tablename__ = 'claims'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    date_of_loss = Column(Date)
    location = Column(String)
    damage_info = Column(JSON)
    weather_ok = Column(Integer)
    approved = Column(Integer)
    notes = Column(String)
    refund_tx = Column(String)

Base.metadata.create_all(engine)
```  

---

### 8. Dockerfile
```dockerfile
FROM python:3.11-slim as base
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libgl1 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```  

---

### 9. docker-compose.yml
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OWM_API_KEY=${OWM_API_KEY}
      - STRIPE_API_KEY=${STRIPE_API_KEY}
    volumes:
      - ./claims.db:/app/claims.db
```  

