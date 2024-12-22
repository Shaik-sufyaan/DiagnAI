import sqlite3

# Step 1: Create an in-memory SQLite database and table for testing
conn = sqlite3.connect(":memory:")  # In-memory database
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE UserData (
    Name TEXT,
    Age INT,
    Sex TEXT,
    Ethnicity TEXT
)
""")

cursor.executemany("""
INSERT INTO UserData (Name, Age, Sex, Ethnicity) VALUES (?, ?, ?, ?)
""", [
    ("Alice", 25, "Female", "Caucasian"),
    ("Bob", 30, "Male", "Asian"),
    ("Charlie", 22, "Male", "Hispanic")
])

print("\nColumnwise Output:")
cursor.execute("SELECT * FROM UserData")
rows = cursor.fetchall()
print(f"Raw Data :\n{rows}\n\n")

print(f"Output of the description function in sqlite3:\n{cursor.description}")
columns = [desc[0] for desc in cursor.description]

for col_index, col_name in enumerate(columns):
    print(f"{col_name}:")
    for row in rows:
        print(f"  {row[col_index]}")
    print()

conn.close()
