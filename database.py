import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME", "ai_study_assistant")
    )


if __name__ == "__main__":
    try:
        connection = get_db_connection()

        if connection.is_connected():
            print("MySQL Database Connected Successfully!")

        connection.close()

    except mysql.connector.Error as error:
        print("Database Connection Failed:", error)