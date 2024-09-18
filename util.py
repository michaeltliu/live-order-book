import random
import string
import timeit
from datetime import datetime

def random_id(length = 8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def generate_salt(length = 8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits + string.ascii_uppercase, k=length))

def repeatArray(arr, k):
    return [arr[i//k] for i in range(k*len(arr))]

def strtime(dt):
    return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')

def stringifyTimes(arr, key):
    return [{**d, key: strtime(d[key])} for d in arr]

def stringifyTime(d, key):
    return {**d, key: strtime(d[key])}