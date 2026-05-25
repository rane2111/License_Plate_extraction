# main.py
import cv2
from ultralytics import YOLO
import re
import os
from datetime import datetime
from PIL import Image
import pytesseract
from collections import Counter
from sql import store_recent_ocr  # ✅ import from sql.py

# ----------------- Configure pytesseract -----------------
import shutil

def find_tesseract():
    """Auto-detect Tesseract executable path."""
    # Check if tesseract is already on PATH
    path = shutil.which("tesseract")
    if path:
        return path
    # Common Windows install locations
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.environ.get("USERNAME", "")),
        r"C:\Users\{}\anaconda3\envs\cvproj\Library\bin\tesseract.exe".format(os.environ.get("USERNAME", "")),
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        "Tesseract not found! Install it from https://github.com/tesseract-ocr/tesseract "
        "or set pytesseract.pytesseract.tesseract_cmd manually."
    )

pytesseract.pytesseract.tesseract_cmd = find_tesseract()

# ----------------- Create required folders -----------------
os.makedirs("crops", exist_ok=True)
os.makedirs("json", exist_ok=True)

# ----------------- OCR Function -----------------
def tesseract_ocr(frame, x1, y1, x2, y2, frame_count):
    pad = 5
    x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
    x2, y2 = x2 + pad, y2 + pad
    crop = frame[y1:y2, x1:x2]
    cv2.imwrite(f"crops/crop_{frame_count}.png", crop)
    img_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text = pytesseract.image_to_string(pil_img, config=config)
    text = re.sub(r'[\W]', '', text).upper().replace("O", "0")
    return text

# ----------------- Process Video -----------------
def extract_plates(video_path):
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    model = YOLO("weights/best.pt")
    count = 0
    frame_plate_counter = Counter()
    start_time = datetime.now()

    plate_pattern = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}$')

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        count += 1
        results = model.predict(frame, conf=0.45)
        frame_plates = set()
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = tesseract_ocr(frame, x1, y1, x2, y2, count)
                if plate_pattern.match(label):
                    frame_plates.add(label)
        for plate in frame_plates:
            frame_plate_counter[plate] += 1

    cap.release()

    # -----------------
    # Save only recent OCR entries
    # -----------------
    consensus_threshold = 3
    valid_plates = [p for p, c in frame_plate_counter.items() if c >= consensus_threshold]
    if valid_plates:
        start_time = datetime.now().isoformat()
        end_time = datetime.now().isoformat()
        ocr_entries = [(start_time, end_time, plate) for plate in valid_plates]
        store_recent_ocr(ocr_entries)  # ✅ replaces old data with latest

    return True
