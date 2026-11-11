from app.database import get_connection

conn = get_connection()
cursor = conn.cursor()

print("=== SUMMARY BY SECTION ===")
cursor.execute("""
    SELECT carriageway, 
           COUNT(*) as total_piers,
           SUM(CASE WHEN status = 'Verified' THEN 1 ELSE 0 END) as verified,
           SUM(CASE WHEN status != 'Verified' THEN 1 ELSE 0 END) as review_needed
    FROM piers
    GROUP BY carriageway
""")
for r in cursor.fetchall():
    print(f"{r['carriageway']:<20}: {r['total_piers']} piers (Verified: {r['verified']}, Review/Unverified: {r['review_needed']})")

print("\n=== TOTAL COUNTS ===")
cursor.execute("SELECT COUNT(*) FROM corner_points")
pts = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM piers")
prs = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM conflicts")
cfs = cursor.fetchone()[0]
print(f"Total Corner Points: {pts}, Total Piers: {prs}, Cross-PDF Conflicts: {cfs}")

print("\n=== SAMPLE PIER CENTRES (10 REQUIRED COLUMNS + STATUS) ===")
cursor.execute("""
    SELECT carriageway, pier_id, point_range, latitude, longitude, distance_from_previous,
           pier_height, pier_width, pier_cap_height, pier_cap_width, status
    FROM piers
    WHERE pier_id IN ('A1', 'P1', 'P2', 'P4', 'P5', 'P6', 'P7', 'Loop1-P1', 'Loop1-P2', 'Loop1-A1', 'Loop2-P1')
    ORDER BY carriageway, sequence_order
    LIMIT 12
""")
for r in cursor.fetchall():
    dist_str = f"{r['distance_from_previous']:.2f}m" if r['distance_from_previous'] is not None else "None (First Pier)"
    print(f"[{r['carriageway']}] {r['pier_id']}: Range={r['point_range']}, Lat={r['latitude']:.8f}, Lon={r['longitude']:.8f}, Dist={dist_str}, Status={r['status']}")

conn.close()
