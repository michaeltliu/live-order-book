import random
import string

def random_id(length = 8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
