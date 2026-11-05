from database import get_db_connection


# SAVE PROMPT HISTORY
def save_prompt_history(student_id, prompt, response):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO prompt_history
            (student_id, prompt, response)
            VALUES (%s, %s, %s)
            """,
            (student_id, prompt, response)
        )

        connection.commit()
        return True

    except Exception as error:
        print("History Save Error:", error)
        return False

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# GET PROMPT HISTORY
def get_prompt_history(student_id):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, prompt, response, created_at
            FROM prompt_history
            WHERE student_id = %s
            ORDER BY created_at DESC
            """,
            (student_id,)
        )

        return cursor.fetchall()

    except Exception as error:
        print("History Fetch Error:", error)
        return []

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()