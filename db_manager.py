import sqlite3
from datetime import datetime

def init_db():
    """Creates a local database file and the necessary table if they do not exist."""
    conn = sqlite3.connect('sparc_history.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prediction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            nitrogen INTEGER,
            phosphorus INTEGER,
            potassium INTEGER,
            temperature REAL,
            rainfall REAL,
            predicted_crop TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_prediction(n, p, k, temp, rain, crop):
    """Inserts a new prediction record into the database."""
    conn = sqlite3.connect('sparc_history.db')
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO prediction_logs 
        (timestamp, nitrogen, phosphorus, potassium, temperature, rainfall, predicted_crop)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (current_time, n, p, k, temp, rain, crop))
    
    conn.commit()
    conn.close()

def fetch_all_logs():
    """Retrieves all historical logs for the dashboard."""
    conn = sqlite3.connect('sparc_history.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prediction_logs ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

init_db()