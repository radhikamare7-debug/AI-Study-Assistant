from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection


def register_student(name, email, password):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Check whether email already exists
        cursor.execute(
            "SELECT id FROM students WHERE email = %s",
            (email,)
        )

        if cursor.fetchone():
            return False, "This email is already registered."

        # Hash password before saving
        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO students (name, email, password_hash)
            VALUES (%s, %s, %s)
            """,
            (name, email, password_hash)
        )

        connection.commit()

        return True, "Registration successful!"

    except Exception as error:
        return False, str(error)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


def login_student(email, password):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM students WHERE email = %s",
            (email,)
        )

        student = cursor.fetchone()

        if student and check_password_hash(
            student["password_hash"],
            password
        ):
            return student

        return None

    except Exception as error:
        print("Login Error:", error)
        return None

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()