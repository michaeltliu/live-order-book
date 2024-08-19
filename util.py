import random
import string
import timeit
from datetime import datetime

def random_id(length = 8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def repeatArray(arr, k):
    return [arr[i//k] for i in range(k*len(arr))]

def strtime(dt):
    return dt.strftime('%d %b %Y %H:%M:%S.%f')