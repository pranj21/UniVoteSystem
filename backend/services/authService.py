import bcrypt

def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt.
    :param password: The password to hash.
    :return: Hashed password as a string.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(input_password: str, stored_password: str) -> bool:
    """
    Verifies a password using bcrypt.
    :param input_password: The password provided by the user.
    :param stored_password: The hashed password stored in the database.
    :return: True if password matches, False otherwise.
    """
    return bcrypt.checkpw(input_password.encode(), stored_password.encode())
