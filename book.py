import heapq
from order import Bid, Ask, Trade
from flask import Flask, request
from flask_cors import CORS
from user import User
from datetime import datetime
import util

app = Flask(__name__)
CORS(app)

users = {}
bids = []
asks = []
trades = []

last_buy_t = []
last_buy_p = []
last_sell_t = []
last_sell_p = []

best_bid_t = []
best_bid_p = []
best_offer_t = []
best_offer_p = []

bt, bp, ot, op = [], [], [], []

def settle_trade(volume, price, buyer, seller, buy_aggr):
    trade = Trade(volume, price, buyer.username, seller.username, buy_aggr)
    buyer.trades.append(trade)
    seller.trades.append(trade)
    trades.append(trade)
    if trade.buy_aggr:
        last_buy_t.append(trade.trade_time)
        last_buy_p.append(trade.price)
    else:
        last_sell_t.append(trade.trade_time)
        last_sell_p.append(trade.price)

    notional = volume * price
    buyer.cash -= notional
    seller.cash += notional
    buyer.position += volume
    seller.position -= volume

def track_bbo(time):
    bbid = 0 if len(bids) == 0 else bids[0].limit
    boffer = 100 if len(asks) == 0 else asks[0].limit
    
    if len(best_bid_p) == 0:
        best_bid_t.append(time)
        best_bid_p.append(bbid)
        best_offer_t.append(time)
        best_offer_p.append(boffer)
        
        bt.append(time)
        bp.append(bbid)
        ot.append(time)
        op.append(boffer)

    elif best_bid_p[-1] == bbid and best_offer_p[-1] == boffer:
        return
    else:
        bt.extend([time, time])
        bp.extend([best_bid_p[-1], bbid])
        ot.extend([time, time])
        op.extend([best_offer_p[-1], boffer])

        best_bid_t.append(time)
        best_bid_p.append(bbid)
        best_offer_t.append(time)
        best_offer_p.append(boffer)

@app.route('/buy/limit/<limit>/quantity/<quantity>/user_id/<user_id>')
def buy(limit, quantity, user_id):
    limit = round(float(limit), 2)
    quantity = int(quantity)

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

    track_bbo(datetime.now())

    return "Success"

@app.route('/sell/limit/<limit>/quantity/<quantity>/user_id/<user_id>')
def sell(limit, quantity, user_id):
    limit = float(limit)
    quantity = int(quantity)

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

    track_bbo(datetime.now())

    return "Success"

@app.route('/delete-order/<order_id>')
def delete_order(order_id):
    for bid in bids:
        if bid.order_id == order_id:
            bids.remove(bid)
            users[bid.user_id].orders.remove(bid)

            track_bbo(datetime.now())
            return "Success"
            
    for ask in asks:
        if ask.order_id == order_id:
            asks.remove(ask)
            users[ask.user_id].orders.remove(ask)

            track_bbo(datetime.now())
            return "Success"

    return "Order number not found"
    
@app.route('/login/<username>')
def handle_login(username):
    print(username)
    
    user = None
    for u in users.values():
        if username == u.username:
            user = u
    if user == None:
        user = User(username)
        users[user.user_id] = user
    
    return user.user_id

@app.route('/user-data/<user_id>')
def get_user_data(user_id):
    if user_id in users:
        return users[user_id].getData()
    else:
        return "User not found"

@app.route('/order-book')
def get_order_book():
    return {
        'bids': [{'limit': b.limit, 'quantity': b.quantity} for b in bids],
        'asks': [{'limit': a.limit, 'quantity': a.quantity} for a in asks]
    }

@app.route('/bbo-history/<index>')
def get_bbo_history(index):
    i = int(index)
    i2 = max(2*i - 1, 0)

    return {
        'bb_t':best_bid_t[i:], 'bb_p':best_bid_p[i:],
        'bo_t':best_offer_t[i:], 'bo_p':best_offer_p[i:],
        'bt':bt[i2:], 'bp':bp[i2:], 
        'ot':ot[i2:], 'op':op[i2:]
    }

@app.route('/last-dones/<b_i>/<s_i>')
def get_last_dones(b_i, s_i):
    b = int(b_i)
    s = int(s_i)
    return {
        'buy_t':last_buy_t[b:], 'buy_p':last_buy_p[b:], 
        'sell_t':last_sell_t[s:], 'sell_p':last_sell_p[s:],
    }


if __name__ == '__main__':
    app.run(port=5000)