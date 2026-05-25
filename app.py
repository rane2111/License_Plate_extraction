import streamlit as st
import os
import sqlite3
import pandas as pd
from main import extract_plates
from sql import compare_plates

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="License Plate Verification", layout="wide")

# ------------------ CUSTOM STYLES ------------------
st.markdown("""
    <style>
        .main {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: white;
        }
        .title {
            font-size: 42px;
            font-weight: bold;
            text-align: center;
            color: #00f5d4;
            margin-bottom: 15px;
        }
        .subtitle {
            text-align: center;
            color: #ffffffaa;
            font-size: 18px;
        }
        .stDataFrame {
            background-color: #1b1b1b;
            border-radius: 10px;
        }
        .card {
            background-color: #1e293b;
            padding: 20px;
            border-radius: 15px;
            margin: 10px 0;
            box-shadow: 0 0 20px rgba(0,0,0,0.3);
            color: white;
        }
        .match-card {
            border-left: 6px solid #22c55e;
        }
        .fraud-card {
            border-left: 6px solid #ef4444;
        }
        .info-card {
            border-left: 6px solid #3b82f6;
        }
        .highlight {
            color: #00f5d4;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------ HEADER ------------------
st.markdown("<div class='title'>🚗 License Plate Verification System</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Upload a vehicle video to extract license plates and verify permit status in real time.</div>", unsafe_allow_html=True)
st.markdown("---")

# ------------------ FILE UPLOAD ------------------
uploaded_file = st.file_uploader("📤 Upload Vehicle Video", type=["mp4", "avi", "mov"])

if uploaded_file:
    os.makedirs("uploaded_videos", exist_ok=True)
    video_path = os.path.join("uploaded_videos", uploaded_file.name)
    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())

    st.success(f"✅ Video uploaded successfully: `{uploaded_file.name}`")

    # ------------------ STEP 1: Extract Plates ------------------
    with st.spinner("🔍 Extracting license plates from video..."):
        extract_plates(video_path)
    st.info("✅ License plates extracted successfully!")

    # ------------------ STEP 2: Compare Plates ------------------
    with st.spinner("🔗 Comparing with registered vehicle database..."):
        compare_plates()
    st.info("✅ Comparison completed!")

    # ------------------ STEP 3: LOAD DATA ------------------
    conn1 = sqlite3.connect("vehicle_permits.db")
    cursor1 = conn1.cursor()
    cursor1.execute("SELECT owner_name, license_plate, permit_validity FROM vehicle_info")
    vehicle_data = cursor1.fetchall()
    conn1.close()

    conn2 = sqlite3.connect("LicensePlatesDatabase.db")
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT license_plate FROM LicensePlates")
    ocr_data = [row[0] for row in cursor2.fetchall()]
    conn2.close()

    # ------------------ STEP 4: COMPARE RESULTS ------------------
    results = []
    for owner_name, plate, validity in vehicle_data:
        status = "MATCH" if plate in ocr_data else "MISMATCH"
        results.append((owner_name, plate, validity, status))

    if results:
        df = pd.DataFrame(results, columns=["Owner Name", "License Plate", "Permit Validity", "Status"])
        matches = df[df["Status"] == "MATCH"]

        # ------------------ DISPLAY MATCHES ------------------
        if not matches.empty:
            st.markdown("<div class='card match-card'>✅ <b>Registered Vehicle Found!</b></div>", unsafe_allow_html=True)
            st.dataframe(matches, use_container_width=True)
            for _, row in matches.iterrows():
                st.markdown(f"""
                <div class='card match-card'>
                    <b>Owner:</b> <span class='highlight'>{row['Owner Name']}</span><br>
                    <b>License Plate:</b> <span class='highlight'>{row['License Plate']}</span><br>
                    <b>Permit Validity:</b> {row['Permit Validity']}
                </div>
                """, unsafe_allow_html=True)
        else:
            # ------------------ DISPLAY FRAUD CASES ------------------
            st.markdown("<div class='card fraud-card'>🚨 <b>Fraud / Unregistered License Plates Detected</b></div>", unsafe_allow_html=True)
            fraud_plates = [plate for plate in ocr_data if plate not in df["License Plate"].values]
            fraud_plates = list(set(fraud_plates))

            if fraud_plates:
                for plate in fraud_plates:
                    st.markdown(f"""
                    <div class='card fraud-card'>
                        <b>Unregistered Plate:</b> <span class='highlight'>{plate}</span> 🚔
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("⚠️ No fraudulent plates detected — please verify OCR extraction accuracy.")
    else:
        st.error("❌ No data available for comparison. Please check your databases.")
