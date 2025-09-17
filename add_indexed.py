import sqlite3
import time

DB_FILE_PATH = 'argo.db'

def add_indexes():
    """Connects to the SQLite database and adds indexes to improve query performance."""
    print(f"➡️ Connecting to database at '{DB_FILE_PATH}'...")
    try:
        conn = sqlite3.connect(DB_FILE_PATH)
        cursor = conn.cursor()
        
        print("➡️ Checking for existing indexes...")
        # Get existing indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        existing_indexes = {row[0] for row in cursor.fetchall()}
        print(f"Found indexes: {existing_indexes if existing_indexes else 'None'}")

        indexes_to_create = {
            'idx_float_id': 'CREATE INDEX idx_float_id ON profiles (float_id);',
            'idx_pres': 'CREATE INDEX idx_pres ON profiles (PRES);',
            'idx_time': 'CREATE INDEX idx_time ON profiles (TIME);'
        }

        for idx_name, sql_command in indexes_to_create.items():
            if idx_name not in existing_indexes:
                print(f"➡️ Creating index '{idx_name}'...")
                start_time = time.time()
                cursor.execute(sql_command)
                end_time = time.time()
                print(f"✅ Index '{idx_name}' created successfully in {end_time - start_time:.2f} seconds.")
            else:
                print(f"🔵 Index '{idx_name}' already exists, skipping.")

        conn.commit()
        conn.close()
        print("\n✅ Database indexing complete.")

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")

if __name__ == '__main__':
    add_indexes()