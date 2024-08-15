import heapq
from order import Bid, Ask, Trade
from flask import Flask, request
from flask_cors import CORS
from user import User
import matplotlib.pyplot as plt
from datetime import datetime

app = Flask(__name__)
CORS(app)

users = {}
bids = []
asks = []
trades = []

def settle_trade(volume, price, buyer, seller, buy_aggr):
    trade = Trade(volume, price, buyer.username, seller.username, buy_aggr)
    buyer.trades.append(trade)
    seller.trades.append(trade)
    trades.append(trade)

    notional = volume * price
    buyer.cash -= notional
    seller.cash += notional
    buyer.position += volume
    seller.position -= volume

@app.route('/buy')
def buy():
    limit = float(request.args.get('limit'))
    quantity = int(request.args.get('quantity'))
    user_id = request.args.get('user_id')
    
    bid = Bid(limit, quantity, user_id)
    buyer = users[user_id]

    while len(asks) > 0 and asks[0].limit <= limit and quantity > 0:
        seller = users[asks[0].user_id]
        volume = min(asks[0].quantity, quantity)
        settle_trade(volume, asks[0].limit, buyer, seller, True)

        quantity -= volume
        asks[0].quantity -= volume
        if asks[0].quantity == 0:
            seller.orders.remove(asks[0])
            heapq.heappop(asks)

    if quantity > 0:
        bid.quantity = quantity
        heapq.heappush(bids, bid)
        buyer.orders.append(bid)

    return "Success"

@app.route('/sell')
def sell():
    limit = float(request.args.get('limit'))
    quantity = int(request.args.get('quantity'))
    user_id = request.args.get('user_id')

    ask = Ask(limit, quantity, user_id)
    seller = users[user_id]

    while len(bids) > 0 and bids[0].limit >= limit and quantity > 0:
        buyer = users[bids[0].user_id]
        volume = min(bids[0].quantity, quantity)
        settle_trade(volume, bids[0].limit, buyer, seller, False)

        quantity -= volume
        bids[0].quantity -= volume
        if bids[0].quantity == 0:
            buyer.orders.remove(bids[0])
            heapq.heappop(bids)

    if quantity > 0:
        ask.quantity = quantity
        heapq.heappush(asks, ask)
        seller.orders.append(ask)

    return "Success"

@app.route('/delete')
def delete_order():
    order_id = request.args.get('order_id')

    for bid in bids:
        if bid.order_id == order_id:
            bids.remove(bid)
            users[bid.user_id].orders.remove(bid)
            return "Success"
    for ask in asks:
        if ask.order_id == order_id:
            asks.remove(ask)
            users[ask.user_id].orders.remove(ask)
            return "Success"

    return "No matching order number"

@app.route('/login')
def handle_login():
    username = request.args.get('username')
    print(username)
    
    user = None
    for u in users.values():
        if username == u.username:
            user = u
    if user == None:
        user = User(username)
        users[user.user_id] = user
    
    return user.getData()

@app.route('/price-history')
def get_price_history():
    buy_t = []
    buy_p = []
    sell_t = []
    sell_p = []
    for trade in trades:
        if trade.buy_aggr:
            buy_t.append(trade.trade_time)
            buy_p.append(trade.price)
        else:
            sell_t.append(trade.trade_time)
            sell_p.append(trade.price)
    
    return [datetime.now()]


if __name__ == '__main__':
    app.run(port=5000)