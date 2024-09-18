import redis
import gevent
from flask import Flask

def handle_message(message):
    print(message)

r = redis.Redis(decode_responses = True)
pubsub = r.pubsub()
pubsub.subscribe(**{'room':handle_message})
pubsub.run_in_thread(sleep_time = 0.01)

app = Flask(__name__)

@app.route('/')
def hello():
    return "hello"

if __name__ == '__main__':
    app.run(port = 5000)