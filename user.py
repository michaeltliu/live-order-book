import util

class User:
    def __init__(self, username, user_id):
        self.username = username
        self.user_id = user_id
        self.cash = 0
        self.position = 0
        self.orders = []
        self.trades = []
        self.sid = set() # Maintains all active sessions for this user in this room

    def getData(self):
        return {
            'username': self.username,
            'user_id': self.user_id,
            'cash': self.cash,
            'position': self.position,
            'orders': [
                {
                    'order_id':order.order_id,
                    'order_sent':util.strtime(order.order_time),
                    'side':order.side,
                    'limit':order.limit, 
                    'quantity':order.quantity
                } for order in self.orders],
            'trades': [
                {
                    'trade_time':util.strtime(trade.trade_time),
                    'buyer_name':trade.buyer_name, 
                    'seller_name':trade.seller_name, 
                    'price':trade.price, 
                    'volume':trade.volume
                } for trade in self.trades],
            'sid': list(self.sid)
            }