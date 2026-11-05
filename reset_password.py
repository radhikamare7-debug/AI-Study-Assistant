from getpass import getpass
from database import get_db_connection
from werkzeug.security import generate_password_hash

email = input("Enter your registered email: ").strip().lower()

new_password = getpass("Enter your new password: ")
confirm_password = getpass("Confirm your new password: ")

if len(new_password) < 8:
    print("Password must contain at least 8 characters.")

elif new_password != confirm_password:
    print("Passwords do not match.")

else:
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        password_hash = generate_password_hash(new_password)

        cursor.execute(
            "UPDATE students SET password_hash = %s WHERE email = %s",
            (password_hash, email)
        )

        connection.commit()

        if cursor.rowcount > 0:
            print("Password updated successfully!")
        else:
            print("Email not found in database.")

    except Exception as error:
        print("Error:", error)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()