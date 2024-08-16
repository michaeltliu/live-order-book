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
            'orders': [
                {
                    'order_id':order.order_id,
                    'side':order.side,
                    'limit':order.limit, 
                    'quantity':order.quantity
                } for order in self.orders
            ],
            'trades': [
                {
                    'buyer_name':trade.buyer_name, 
                    'seller_name':trade.seller_name, 
                    'price':trade.price, 
                    'volume':trade.volume
                } for trade in self.trades
            ]
        }