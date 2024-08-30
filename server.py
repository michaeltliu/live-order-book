import heapq
from order import Bid, Ask, Trade
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from profile import Profile
from room import Room
from user import User
from datetime import datetime
import util
import redis

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

redis_client = redis.Redis(decode_responses = True)

rooms = {} # All existing rooms {room_id: Room}
profiles = {} # All existing profiles {user_id: Profile}
sessions = {} # All existing sessions and corresponding room, '' indicates SelectRoomView {sid: room_id}
# Might want map from session id to user id

def emit_set(event, data, sid_set):
    for sid in sid_set:
        socketio.emit(event, data, to=sid)

def get_room_and_user(sid):
    room_id = sessions[sid]
    room = rooms[room_id]
    user_id = room.sessions[sid]
    user = room.users[user_id]

    return room_id, room, user_id, user

@app.route('/login/<username>')
def handle_login(username):    
    profile = None
    for p in profiles.values():
        if username == p.username:
            profile = p
    if profile == None:
        profile = Profile(username)
        profiles[profile.user_id] = profile

    return {'user_id':profile.user_id, 'rooms':list(profile.rooms)}

@socketio.on('connect')
def handle_connect():    
    print('Client connected')

@socketio.on('create-room')
def create_room(room_name):
    room = Room(room_name)
    rooms[room.room_id] = room
    print(room.room_id)
    return room.room_id

@socketio.on('join-room')    
def join_room(room_id, user_id):
    print('in join room')
    profile = profiles[user_id]
    room = rooms[room_id]
    if room_id in profile.rooms:
        user = room.users[user_id]
        user.sid.add(request.sid)
    else:
        user = User(profile.username, profile.user_id)
        user.sid.add(request.sid)
        room.users[user_id] = user
        profile.rooms.add(room_id)
        emit('update_user_data', {'user_id': user_id, 'rooms': list(profile.rooms)})

    room.sessions[request.sid] = user_id
    sessions[request.sid] = room_id

    return {
        'room_id': room_id, 
        'user_data': user.getData(),
        'bbo_history': get_bbo_history(room_id, 0),
        'ld_history':get_last_dones(room_id, 0, 0)
        }

@socketio.on('exit-room')
def exit_room():
    room_id, room, user_id, user = get_room_and_user(request.sid)

    user.sid.remove(request.sid)
    room.sessions.pop(request.sid)
    sessions.pop(request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in sessions:
        exit_room()
    print('Client disconnected')

@app.route('/sessions/<room_id>/<user_id>')
def get_sessions(room_id, user_id):
    room = rooms[room_id]
    users = room.users
    return list(users[user_id].sid)

def settle_trade(room, volume, price, buyer, seller, buy_aggr):
    trade = Trade(volume, price, buyer.username, seller.username, buy_aggr)
    buyer.trades.append(trade)
    seller.trades.append(trade)
    room.trades.append(trade)

    if buy_aggr:
        room.last_buy_t.append(util.strtime(trade.trade_time))
        room.last_buy_p.append(price)
    else:
        room.last_sell_t.append(util.strtime(trade.trade_time))
        room.last_sell_p.append(price)

    notional = volume * price
    buyer.cash -= notional
    seller.cash += notional
    buyer.position += volume
    seller.position -= volume

def track_bbo(room, time):
    time = util.strtime(time)
    bids = room.bids
    asks = room.asks
    best_bid_t = room.best_bid_t
    best_bid_p = room.best_bid_p
    best_offer_t = room.best_offer_t
    best_offer_p = room.best_offer_p
    bt = room.bt
    bp = room.bp
    ot = room.ot
    op = room.op

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

@socketio.on('buy')
def buy(limit, quantity):
    room_id, room, user_id, buyer = get_room_and_user(request.sid)
    users = room.users
    bids = room.bids
    asks = room.asks

    limit = round(float(limit), 2)
    quantity = int(quantity)
    bid = Bid(limit, quantity, user_id)

    traded = False

    while len(asks) > 0 and asks[0].limit <= limit and quantity > 0:
        traded = True
        seller = users[asks[0].user_id]
        volume = min(asks[0].quantity, quantity)
        settle_trade(room, volume, asks[0].limit, buyer, seller, True)

        quantity -= volume
        asks[0].quantity -= volume
        if asks[0].quantity == 0:
            seller.orders.remove(asks[0])
            heapq.heappop(asks)

        emit_set('update_roomuser_data', seller.getData(), seller.sid)
        emit_set('update_roomuser_data', buyer.getData(), buyer.sid)

        # TODO: Associate a user's trade with its order

    if quantity > 0:
        bid.quantity = quantity
        heapq.heappush(bids, bid)
        buyer.orders.append(bid)
        emit_set('update_roomuser_data', buyer.getData(), buyer.sid)
        print('hi', buyer.getData(), buyer.sid)

    if track_bbo(room, datetime.now()):
        emit_set('update_bbo_history', get_bbo_history(room_id, room.bbo_broadcast_i), room.sessions.keys())
        room.bbo_broadcast_i = len(room.best_bid_p)

    if traded:
        emit_set('update_ld_history', get_last_dones(room_id, room.lb_broadcast_i, room.ls_broadcast_i), room.sessions.keys())
        room.lb_broadcast_i = len(room.last_buy_p)
        room.ls_broadcast_i = len(room.last_sell_p)

    return "Success"

@socketio.on('sell')
def sell(limit, quantity):
    room_id, room, user_id, seller = get_room_and_user(request.sid)
    users = room.users
    bids = room.bids
    asks = room.asks

    limit = round(float(limit), 2)
    quantity = int(quantity)
    ask = Ask(limit, quantity, user_id)

    traded = False

    while len(bids) > 0 and bids[0].limit >= limit and quantity > 0:
        traded = True
        buyer = users[bids[0].user_id]
        volume = min(bids[0].quantity, quantity)
        settle_trade(room, volume, bids[0].limit, buyer, seller, False)

        quantity -= volume
        bids[0].quantity -= volume
        if bids[0].quantity == 0:
            buyer.orders.remove(bids[0])
            heapq.heappop(bids)

        emit_set('update_roomuser_data', buyer.getData(), buyer.sid)
        emit_set('update_roomuser_data', seller.getData(), seller.sid)

        # TODO: Associate a user's trade with its order

    if quantity > 0:
        ask.quantity = quantity
        heapq.heappush(asks, ask)
        seller.orders.append(ask)
        emit_set('update_roomuser_data', seller.getData(), seller.sid)

    if track_bbo(room, datetime.now()):
        emit_set('update_bbo_history', get_bbo_history(room_id, room.bbo_broadcast_i), room.sessions.keys())
        room.bbo_broadcast_i = len(room.best_bid_p)

    if traded:
        emit_set('update_ld_history', get_last_dones(room_id, room.lb_broadcast_i, room.ls_broadcast_i), room.sessions.keys())
        room.lb_broadcast_i = len(room.last_buy_p)
        room.ls_broadcast_i = len(room.last_sell_p)

    return "Success"

@socketio.on('delete')
def delete_order(order_id):
    room_id, room, user_id, user = get_room_and_user(request.sid)
    users = room.users
    bids = room.bids
    asks = room.asks

    for bid in bids:
        if bid.order_id == order_id:
            bids.remove(bid)
            user.orders.remove(bid)
            emit_set('update_roomuser_data', user.getData(), user.sid)

            if track_bbo(room, datetime.now()):
                emit_set('update_bbo_history', get_bbo_history(room_id, room.bbo_broadcast_i), room.sessions.keys())
                room.bbo_broadcast_i = len(room.best_bid_p)
            return "Success"
            
    for ask in asks:
        if ask.order_id == order_id:
            asks.remove(ask)
            user.orders.remove(ask)
            emit_set('update_roomuser_data', user.getData(), user.sid)

            if track_bbo(room, datetime.now()):
                emit_set('update_bbo_history', get_bbo_history(room_id, room.bbo_broadcast_i), room.sessions.keys())
                room.bbo_broadcast_i = len(room.best_bid_p)
            return "Success"

    return "Order number not found" # These return statements are never used

@app.route('/user-data/<room_id>/<user_id>')
def get_user_data(room_id, user_id):
    room = rooms[room_id]
    if user_id in room.users:
        return room.users[user_id].getData()
    else:
        return "User not found"

@app.route('/bbo-history/<room_id>/<index>')
def get_bbo_history(room_id, index):
    room = rooms[room_id]
    i = int(index)
    i2 = max(2*i - 1, 0)

    return {
        'bb_t': room.best_bid_t[i:], 'bb_p': room.best_bid_p[i:],
        'bo_t': room.best_offer_t[i:], 'bo_p': room.best_offer_p[i:],
        'bt': room.bt[i2:], 'bp': room.bp[i2:], 
        'ot': room.ot[i2:], 'op': room.op[i2:]
    }

@app.route('/last-dones/<room_id>/<b_i>/<s_i>')
def get_last_dones(room_id, b_i, s_i):
    room = rooms[room_id]
    b = int(b_i)
    s = int(s_i)
    return {
        'buy_t': room.last_buy_t[b:], 'buy_p': room.last_buy_p[b:], 
        'sell_t': room.last_sell_t[s:], 'sell_p': room.last_sell_p[s:],
    }

@app.route('/order-book/<room_id>')
def get_order_book(room_id):
    room = rooms[room_id]
    return {
        'bids': [{'limit': b.limit, 'quantity': b.quantity} for b in room.bids],
        'asks': [{'limit': a.limit, 'quantity': a.quantity} for a in room.asks]
    }


if __name__ == '__main__':
    socketio.run(app, port=5000, allow_unsafe_werkzeug=True)
