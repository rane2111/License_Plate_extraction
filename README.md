# License Plate Extraction & Verification System

A Streamlit-based application that extracts license plates from vehicle videos using **YOLOv10** + **Tesseract OCR** and verifies them against a registered vehicle database stored in **SQLite**.

---

## 📋 Project Description

This system provides automated license plate detection, recognition, and verification. It is designed to process security footage or vehicle dashcam videos, extract license plates in real time, run OCR to digitize the alphanumeric characters, and perform instant lookup validations against a state/permit database.

### Core Architecture & Workflow
1. **Video Stream Processing**: The Streamlit frontend accepts uploads of common video formats (`.mp4`, `.avi`, `.mov`).
2. **AI-Powered Plate Detection**: Frames are analyzed sequentially by a custom-trained **YOLOv10** model to identify license plate boundary boxes.
3. **Robust Alphanumeric OCR**: Detected license plate regions are cropped and sent to **Tesseract OCR** configured with whitelist rules to extract plate numbers cleanly.
4. **Consensus Filter Logic**: To avoid false positives and noise from low-resolution frames, a consensus threshold (default: `3` appearances) is applied before flagging a license plate as successfully read.
5. **Permit Cross-Verification**: Extracted plates are saved to `LicensePlatesDatabase.db` and cross-referenced with `vehicle_permits.db` via SQL database joins.
6. **Real-time Status Alert UI**: Plates are flagged as **MATCH** (Registered owner details & permit validity displayed) or **🚨 FRAUD** (Unregistered vehicle plate detected).

---

## 🛠️ Prerequisites

- Python 3.11+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed on your system.
- Conda (recommended) or pip virtual environment.

---

## 🚀 Setup & Run Instructions

```bash
# 1. Clone the repository
git clone https://github.com/entbappy/License-Plate-Extraction-Save-Data-to-SQL-Database.git
cd License-Plate-Extraction-Save-Data-to-SQL-Database

# 2. Create and activate a conda environment
conda create -n cvproj python=3.11 -y
conda activate cvproj

# 3. Install the YOLOv10 dependency package
cd yolov10
pip install -e .
cd ..

# 4. Install project requirements
pip install -r requirements.txt

# 5. Initialize the databases (run once at first boot)
python -c "from sql import setup_databases; setup_databases()"

# 6. Start the Streamlit application
streamlit run app.py
```

The web application will launch and open in your default browser at **`http://localhost:8501`**.

---

## 📂 Project Structure

```
├── app.py                    # Streamlit web interface and user workflow logic
├── main.py                   # Custom YOLOv10 predictor and Tesseract OCR processor
├── sql.py                    # SQLite tables manager, consensus writer, and query compare engine
├── requirements.txt          # Complete verified python library dependencies
├── .gitignore                # Configured to ignore transient runtime data and caches
├── weights/
│   └── best.pt               # Custom trained YOLOv10 weights for license plate boundary box detection
├── data/                     # Sample vehicle video tracks for local pipeline testing
├── vehicle_permits.db        # Static SQLite database storing registered owners and valid plates
├── licensePlatesDatabase.db  # Runtime SQLite database containing OCR results and matches
└── yolov10/                  # YOLOv10 neural network library dependency
```

---

## 🔧 Troubleshooting

**NumPy Version Compatibility Mismatch:**
```bash
pip uninstall numpy -y
pip install numpy==1.26.4
```

**Tesseract OCR Executable Not Found:**
Ensure Tesseract is installed and in your environment `PATH`. If not, `main.py` is equipped to automatically scan common install directories:
- `C:\Program Files\Tesseract-OCR\tesseract.exe`
- `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`

**Visualizing Database Records:**
You can view database tables cleanly using the [Online SQLite Viewer](https://inloop.github.io/sqlite-viewer/).
<img width="1920" height="1020" alt="Screenshot 2026-05-25 213315" src="https://github.com/user-attachments/assets/78fdfd84-6df2-41d9-8894-62877227fb2d" />
<img width="1920" height="1020" alt="Screenshot 2026-05-25 215142" src="https://github.com/user-attachments/assets/f800c9ac-10a9-44f9-a113-3dff60034a73" />
