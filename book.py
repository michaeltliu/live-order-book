import heapq
from order import Bid, Ask, Trade
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from user import User
from room import Room
from roomuser import RoomUser
from datetime import datetime
import util

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

users = {}
sessions = {}

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

lb_broadcast_i = 0
ls_broadcast_i = 0
bbo_broadcast_i = 0

#DONE
def emit_set(event, data, sid_set):
    for sid in sid_set:
        socketio.emit(event, data, to=sid)

# DONE
# Updates buyer and seller's data and logs last done
def settle_trade(room, volume, price, buyer, seller, buy_aggr):
    trade = Trade(volume, price, buyer.username, seller.username, buy_aggr)
    buyer.trades.append(trade)
    seller.trades.append(trade)
    trades.append(trade)
    if trade.buy_aggr:
        last_buy_t.append(util.strtime(trade.trade_time))
        last_buy_p.append(trade.price)
    else:
        last_sell_t.append(util.strtime(trade.trade_time))
        last_sell_p.append(trade.price)

    notional = volume * price
    buyer.cash -= notional
    seller.cash += notional
    buyer.position += volume
    seller.position -= volume

#DONE
def track_bbo(room_id, time):
    time = util.strtime(time)
    bbid = 0 if len(bids) == 0 else bids[0].limit
    boffer = 100 if len(asks) == 0 else asks[0].limit
    
    if len(best_bid_p) == 0:
        # BBO is empty so add first point to plot
        best_bid_t.append(time)
        best_bid_p.append(bbid)
        best_offer_t.append(time)
        best_offer_p.append(boffer)
        
        bt.append(time)
        bp.append(bbid)
        ot.append(time)
        op.append(boffer)

        return True

    elif best_bid_p[-1] == bbid and best_offer_p[-1] == boffer:
        # BBO is unchanged
        return False
    else:
        # BBO is nonempty so add point and draw line
        bt.extend([time, time])
        bp.extend([best_bid_p[-1], bbid])
        ot.extend([time, time])
        op.extend([best_offer_p[-1], boffer])

        best_bid_t.append(time)
        best_bid_p.append(bbid)
        best_offer_t.append(time)
        best_offer_p.append(boffer)

        return True

@socketio.on('connect')
def handle_connect(auth):
    user_id = auth['user_id']
    user = users[user_id]
    user.sid.add(request.sid)
    sessions[request.sid] = user.user_id

    emit('update_bbo_history', get_bbo_history(0))
    emit('update_ld_history', get_last_dones(0,0))

    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    users[sessions[request.sid]].sid.remove(request.sid)
    sessions.pop(request.sid)
    print('Client disconnected')

@app.route('/sessions/<user_id>')
def get_sessions(user_id):
    print(users[user_id].sid)

# DONE
@app.route('/buy/room/<room_id>/limit/<limit>/quantity/<quantity>/user_id/<user_id>')
def buy(room_id, limit, quantity, user_id):
    global bbo_broadcast_i
    global lb_broadcast_i
    global ls_broadcast_i

    room = rooms[room_id]
    users = room.users
    bids = room.bids
    asks = room.asks

    limit = round(float(limit), 2)
    quantity = int(quantity)

    bid = Bid(limit, quantity, user_id)
    buyer = users[user_id]

    traded = False

    while len(asks) > 0 and asks[0].limit <= limit and quantity > 0:
        traded = True
        seller = users[asks[0].user_id]
        volume = min(asks[0].quantity, quantity)
        settle_trade(volume, asks[0].limit, buyer, seller, True)

        quantity -= volume
        asks[0].quantity -= volume
        if asks[0].quantity == 0:
            seller.orders.remove(asks[0])
            heapq.heappop(asks)

        emit_set('update_user_data', seller.getData(), seller.sid)
        emit_set('update_user_data', buyer.getData(), buyer.sid)

        # TODO: Associate a user's trade with its order

    if quantity > 0:
        bid.quantity = quantity
        heapq.heappush(bids, bid)
        buyer.orders.append(bid)
        emit_set('update_user_data', buyer.getData(), buyer.sid)

    if track_bbo(datetime.now()):
        socketio.emit('update_bbo_history', get_bbo_history(room, bbo_broadcast_i))
        room.bbo_broadcast_i = len(room.best_bid_p)

    if traded:
        socketio.emit('update_ld_history', get_last_dones(lb_broadcast_i, ls_broadcast_i))
        room.lb_broadcast_i = len(room.last_buy_p)
        room.ls_broadcast_i = len(room.last_sell_p)

    return "Success"

# DONE
@app.route('/sell/room/<room_id>/limit/<limit>/quantity/<quantity>/user_id/<user_id>')
def sell(room_id, limit, quantity, user_id):
    global bbo_broadcast_i
    global lb_broadcast_i
    global ls_broadcast_i

    limit = float(limit)
    quantity = int(quantity)

    ask = Ask(limit, quantity, user_id)
    seller = users[user_id]

    traded = False

    while len(bids) > 0 and bids[0].limit >= limit and quantity > 0:
        traded = True
        buyer = users[bids[0].user_id]
        volume = min(bids[0].quantity, quantity)
        settle_trade(volume, bids[0].limit, buyer, seller, False)

        quantity -= volume
        bids[0].quantity -= volume
        if bids[0].quantity == 0:
            buyer.orders.remove(bids[0])
            heapq.heappop(bids)

        emit_set('update_user_data', buyer.getData(), buyer.sid)
        emit_set('update_user_data', seller.getData(), seller.sid)

        # TODO: Associate a user's trade with its order

    if quantity > 0:
        ask.quantity = quantity
        heapq.heappush(asks, ask)
        seller.orders.append(ask)
        emit_set('update_user_data', seller.getData(), seller.sid)

    if track_bbo(datetime.now()):
        socketio.emit('update_bbo_history', get_bbo_history(bbo_broadcast_i))
        bbo_broadcast_i = len(best_bid_p)
    if traded:
        socketio.emit('update_ld_history', get_last_dones(lb_broadcast_i, ls_broadcast_i))
        lb_broadcast_i = len(last_buy_p)
        ls_broadcast_i = len(last_sell_p)

    return "Success"

# DONE
@app.route('/delete-order/<order_id>')
def delete_order(room_id, order_id):
    global bbo_broadcast_i

    for bid in bids:
        if bid.order_id == order_id:
            bids.remove(bid)
            users[bid.user_id].orders.remove(bid)
            emit_set('update_user_data', users[bid.user_id].getData(), users[bid.user_id].sid)

            if track_bbo(datetime.now()):
                socketio.emit('update_bbo_history', get_bbo_history(bbo_broadcast_i))
                bbo_broadcast_i = len(best_bid_p)
            return "Success"
            
    for ask in asks:
        if ask.order_id == order_id:
            asks.remove(ask)
            users[ask.user_id].orders.remove(ask)
            emit_set('update_user_data', users[ask.user_id].getData(), users[ask.user_id].sid)

            if track_bbo(datetime.now()):
                socketio.emit('update_bbo_history', get_bbo_history(bbo_broadcast_i))
                bbo_broadcast_i = len(best_bid_p)
            return "Success"

    return "Order number not found" # These return statements are never used
    
#DONE
@app.route('/login/<username>')
def handle_login(username):    
    user = None
    for u in users.values():
        if username == u.username:
            user = u
    if user == None:
        user = User(username)
        users[user.user_id] = user

    return user.user_id

#DONE
@app.route('/user-data/<user_id>')
def get_user_data(user_id):
    if user_id in users:
        return users[user_id].getData()
    else:
        return "User not found"

#DONE
@app.route('/order-book')
def get_order_book(room_id):
    return {
        'bids': [{'limit': b.limit, 'quantity': b.quantity} for b in bids],
        'asks': [{'limit': a.limit, 'quantity': a.quantity} for a in asks]
    }

#DONE
@app.route('/bbo-history/<index>')
def get_bbo_history(room_id, index):
    i = int(index)
    i2 = max(2*i - 1, 0)

    return {
        'bb_t':best_bid_t[i:], 'bb_p':best_bid_p[i:],
        'bo_t':best_offer_t[i:], 'bo_p':best_offer_p[i:],
        'bt':bt[i2:], 'bp':bp[i2:], 
        'ot':ot[i2:], 'op':op[i2:]
    }

#DONE
@app.route('/last-dones/<b_i>/<s_i>')
def get_last_dones(room_id, b_i, s_i):
    b = int(b_i)
    s = int(s_i)
    return {
        'buy_t':last_buy_t[b:], 'buy_p':last_buy_p[b:], 
        'sell_t':last_sell_t[s:], 'sell_p':last_sell_p[s:],
    }


if __name__ == '__main__':
    socketio.run(app, port=5000)