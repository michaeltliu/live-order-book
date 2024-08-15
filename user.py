import util

class User:
    def __init__(self, username):
        self.username = username
        self.user_id = util.random_id()
        self.cash = 0
        self.position = 0
        self.orders = []
        self.trades = []

    def getData(self):
        return {
            'username': self.username,
            'user_id': self.user_id,
            'cash': self.cash,
            'position': self.position,
            'orders': self.orders,
            'trades': self.trades
        }