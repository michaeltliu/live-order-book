import util

class User:
    def __init__(self, username):
        self.username = username
        self.user_id = util.random_id()
        self.cash = 0
        self.position = 0
        self.orders = []
        self.trades = []