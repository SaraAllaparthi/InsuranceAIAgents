import torch
from PIL import Image
import io

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
CATEGORY_MAPPING = {0: 'rain_damage', 1: 'fire_damage', 2: 'other'}

def analyze_damage(uploaded_file):
    img = Image.open(io.BytesIO(uploaded_file.read()))
    results = model(img)
    det = results.xyxy[0]
    if len(det) == 0:
        return {"type": "unknown", "estimate": 0}
    cls = int(det[0,5])
    damage_type = CATEGORY_MAPPING.get(cls, 'other')
    area = (det[0,2]-det[0,0]) * (det[0,3]-det[0,1])
    estimate = max(500, min(5000, int(area/1000)))
    return {"type": damage_type, "estimate": estimate}
