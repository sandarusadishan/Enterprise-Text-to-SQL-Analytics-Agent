import os
import pyodbc
from database.connection import get_db_connection

try:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("========================================")
    print("🔍 DIAGNOSING DATABASE DATA")
    print("========================================")
    
    # 1. Search for RSV in Master1
    print("\n1. Searching Master1 for 'RSV'...")
    cursor.execute("SELECT Code, Name, Alias FROM Master1 WHERE Name LIKE '%RSV%' OR Alias LIKE '%RSV%'")
    rows = cursor.fetchall()
    if rows:
        for r in rows:
            print(f"   Code: {r[0]} | Name: {r[1]} | Alias: {r[2]}")
    else:
        print("   ❌ No records containing 'RSV' found in Master1.")
        
    # 2. Print first 10 Masters
    print("\n2. First 10 Masters in Master1:")
    cursor.execute("SELECT TOP 10 Code, Name, Alias FROM Master1")
    rows = cursor.fetchall()
    for r in rows:
        print(f"   Code: {r[0]} | Name: {r[1]} | Alias: {r[2]}")
        
    # 3. Print TranTypes in Tran1
    print("\n3. Transaction Types (TranType) and counts in Tran1:")
    cursor.execute("SELECT TranType, COUNT(*) FROM Tran1 GROUP BY TranType")
    rows = cursor.fetchall()
    for r in rows:
        print(f"   TranType: {r[0]} | Count: {r[1]}")
        
    # 4. Check if there are any transactions for the RSV codes found (if any)
    cursor.execute("SELECT Code FROM Master1 WHERE Name LIKE '%RSV%' OR Alias LIKE '%RSV%'")
    rsv_codes = [r[0] for r in cursor.fetchall()]
    if rsv_codes:
        print(f"\n4. Checking transactions for RSV Codes: {rsv_codes}")
        placeholders = ",".join(["?"] * len(rsv_codes))
        cursor.execute(f"SELECT COUNT(*) FROM Tran1 WHERE MasterCode1 IN ({placeholders})", rsv_codes)
        count1 = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM Tran1 WHERE MasterCode2 IN ({placeholders})", rsv_codes)
        count2 = cursor.fetchone()[0]
        print(f"   Transactions as MasterCode1: {count1}")
        print(f"   Transactions as MasterCode2: {count2}")
        
    # 5. Find Master Codes that actually have transactions in Tran1
    print("\n5. Master Codes (MasterCode1) with the most transactions in Tran1:")
    cursor.execute("""
        SELECT TOP 5 t.MasterCode1, m.Name, COUNT(*) as TxnCount 
        FROM Tran1 t
        LEFT JOIN Master1 m ON t.MasterCode1 = m.Code
        GROUP BY t.MasterCode1, m.Name
        ORDER BY TxnCount DESC
    """)
    rows = cursor.fetchall()
    for r in rows:
        print(f"   MasterCode1: {r[0]} | Name: {r[1]} | Transaction Count: {r[2]}")
        
    print("\n6. Master Codes (MasterCode2) with the most transactions in Tran1:")
    cursor.execute("""
        SELECT TOP 5 t.MasterCode2, m.Name, COUNT(*) as TxnCount 
        FROM Tran1 t
        LEFT JOIN Master1 m ON t.MasterCode2 = m.Code
        GROUP BY t.MasterCode2, m.Name
        ORDER BY TxnCount DESC
    """)
    rows = cursor.fetchall()
    for r in rows:
        print(f"   MasterCode2: {r[0]} | Name: {r[1]} | Transaction Count: {r[2]}")
        
    # 7. Print 5 sample transactions from Tran1 to see their values
    print("\n7. Sample transactions from Tran1:")
    cursor.execute("SELECT TOP 5 VchNo, Date, MasterCode1, MasterCode2, VchAmtBaseCur, TranType FROM Tran1")
    rows = cursor.fetchall()
    for r in rows:
        print(f"   VchNo: {r[0]} | Date: {r[1]} | MasterCode1: {r[2]} | MasterCode2: {r[3]} | Amount: {r[4]} | TranType: {r[5]}")

    conn.close()
    print("\n========================================")
    
except Exception as e:
    print(f"❌ Error during diagnosis: {e}")
