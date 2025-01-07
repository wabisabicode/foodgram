import random
import string


def generate_random_filename(length=16):
    """Generates a random filename"""
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string
