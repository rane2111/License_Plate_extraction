import sqlite3

# -------------------- STEP 1: Create Tables --------------------
def setup_databases():
    """
    Create both vehicle_permits and LicensePlates databases with required tables.
    Run this once at the start of your project.
    """
    # ---- Vehicle Permits Database ----
    conn1 = sqlite3.connect("vehicle_permits.db")
    cursor1 = conn1.cursor()
    cursor1.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name TEXT NOT NULL,
            license_plate TEXT UNIQUE NOT NULL,
            permit_validity TEXT NOT NULL
        )
    """)
    conn1.commit()
    conn1.close()

    # ---- OCR Database ----
    conn2 = sqlite3.connect("LicensePlatesDatabase.db")
    cursor2 = conn2.cursor()
    cursor2.execute("""
        CREATE TABLE IF NOT EXISTS LicensePlates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            license_plate TEXT NOT NULL
        )
    """)
    conn2.commit()
    conn2.close()

    print("[SUCCESS] Databases and tables are ready.")


# -------------------- STEP 2: Store OCR Results --------------------
def store_recent_ocr(ocr_entries):
    """
    Stores recent OCR license plates in LicensePlatesDatabase.db.
    Deletes previous entries before inserting new data.
    ocr_entries: list of tuples -> [(start_time, end_time, license_plate), ...]
    """
    conn = sqlite3.connect("LicensePlatesDatabase.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM LicensePlates")  # clear old data
    cursor.executemany("""
        INSERT INTO LicensePlates (start_time, end_time, license_plate)
        VALUES (?, ?, ?)
    """, ocr_entries)

    conn.commit()
    conn.close()
    print("[SUCCESS] OCR entries stored successfully.")


# -------------------- STEP 3: Compare Plates --------------------
def compare_plates():
    """
    Compare license_plate column between vehicle_permits.db and LicensePlatesDatabase.db.
    Stores results in LicensePlatesDatabase.db (comparison_results table).
    Returns list of tuples: (license_plate, owner_name, permit_validity, status)
    """
    # Connect to OCR DB first (it will store the comparison results)
    conn = sqlite3.connect("LicensePlatesDatabase.db")
    cursor = conn.cursor()

    # Attach the vehicle permits DB
    conn.execute("ATTACH DATABASE 'vehicle_permits.db' AS permit_db")

    # Create or reset comparison_results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparison_results (
            license_plate TEXT,
            owner_name TEXT,
            permit_validity TEXT,
            status TEXT
        )
    """)
    cursor.execute("DELETE FROM comparison_results")

    # 1️⃣ Plates present in both DBs → MATCH
    cursor.execute("""
        INSERT INTO comparison_results (license_plate, owner_name, permit_validity, status)
        SELECT o.license_plate, v.owner_name, v.permit_validity, 'MATCH'
        FROM permit_db.vehicle_info v
        INNER JOIN LicensePlates o
        ON UPPER(TRIM(v.license_plate)) = UPPER(TRIM(o.license_plate));
    """)

    # 2️⃣ OCR plates not found in permit DB → MISMATCH
    cursor.execute("""
        INSERT INTO comparison_results (license_plate, owner_name, permit_validity, status)
        SELECT o.license_plate, NULL, NULL, 'MISMATCH (Unregistered)'
        FROM LicensePlates o
        LEFT JOIN permit_db.vehicle_info v
        ON UPPER(TRIM(o.license_plate)) = UPPER(TRIM(v.license_plate))
        WHERE v.license_plate IS NULL;
    """)

    # 3️⃣ Permit DB plates not detected by OCR → MISSING
    cursor.execute("""
        INSERT INTO comparison_results (license_plate, owner_name, permit_validity, status)
        SELECT v.license_plate, v.owner_name, v.permit_validity, 'MISSING (Not detected)'
        FROM permit_db.vehicle_info v
        LEFT JOIN LicensePlates o
        ON UPPER(TRIM(v.license_plate)) = UPPER(TRIM(o.license_plate))
        WHERE o.license_plate IS NULL;
    """)

    conn.commit()

    # Fetch and return all results
    cursor.execute("SELECT * FROM comparison_results")
    results = cursor.fetchall()

    conn.close()
    print("[SUCCESS] Comparison completed successfully.")
    return results


# -------------------- STEP 4: (Optional) View Results --------------------
def view_results():
    """Display all comparison results stored in LicensePlatesDatabase.db"""
    conn = sqlite3.connect("LicensePlatesDatabase.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT license_plate, owner_name, permit_validity, status
        FROM comparison_results
    """)
    results = cursor.fetchall()
    conn.close()

    print("\n📊 Comparison Results:")
    for row in results:
        print(row)


