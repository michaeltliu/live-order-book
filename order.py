import util
from datetime import datetime

class Bid:
    def __init__(self, limit, quantity, user_id):
        self.limit = limit
        self.order_time = datetime.now()
        self.quantity = quantity
        self.order_id = util.random_id()
        self.user_id = user_id

    def __repr__(self):
        return f'Bid {self.quantity} @ LMT {self.limit} by {self.user_id}'

    def __eq__(self, other):
        return (self.limit, self.order_time, self.order_id) == (other.limit, other.order_time, other.order_id)
    
    def __lt__(self, other):
        return (-self.limit, self.order_time, self.order_id) < (-other.limit, other.order_time, other.order_id)

class Ask:
    def __init__(self, limit, quantity, user_id):
        self.limit = limit
        self.order_time = datetime.now()
        self.quantity = quantity
        self.order_id = util.random_id()
        self.user_id = user_id

    def __repr__(self):
        return f'Ask {self.quantity} @ LMT {self.limit} by {self.user_id}'

    def __eq__(self, other):
        return (self.limit, self.order_time, self.order_id) == (other.limit, other.order_time, other.order_id)
    
    def __lt__(self, other):
        return (self.limit, self.order_time, self.order_id) < (other.limit, other.order_time, other.order_id)

class Trade:
    def __init__(self, volume, price, buyer_name, seller_name, buy_aggr):
        self.trade_time = datetime.now()
        self.volume = volume
        self.price = price
        self.buyer_name = buyer_name
        self.seller_name = seller_name
        self.buy_aggr = buy_aggr

    def __repr__(self):
        if buy_aggr:
            f'{self.buyer_name} BOT {self.volume} lots @ {self.price}'
        else:
            f'{self.seller_name} SOLD {self.volume} lots @ {self.price}'