from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import util
#import redis
import os
from hashlib import sha256
from db_connector import DB_Connector

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# redis_client = redis.Redis(decode_responses = True)

session_to_user = {}
user_to_sessions = {}
room_to_sessions = {}
session_to_profile = {}
token_to_profile = {}

def emit_set(event, data, sid_set):
    for sid in sid_set:
        socketio.emit(event, data, to=sid)

@app.route('/login', methods = ['POST'])
def handle_login():
    data = request.get_json()
    username = data.get('username').lower()
    password = data.get('password')
    print('handle_login', username)

    with DB_Connector() as db:
        d = db.get_profile(username)
        if d:
            if sha256((password + d['salt']).encode('utf-8')).hexdigest() == d['sha']:
                profile_id = d['id']
                rooms = db.get_profile_rooms(d['id'])
            else:
                return {'status': False}
        else:
            salt = util.generate_salt()
            sha = sha256((password + salt).encode('utf-8')).hexdigest()
            profile_id = db.add_profile(username, salt, sha)
            if not profile_id:
                return {'status': False}
            rooms = []
        
    time = datetime.now()
    nonce = "%s %s %s" % (os.environ.get('APP_KEY'), profile_id, time)
    token = sha256(nonce.encode('utf-8')).hexdigest()
    token_to_profile[token] = (profile_id, time)

    return {
        'status': True,
        'profile_id': profile_id,
        'token': token,
        'rooms': rooms
        }

@socketio.on('connect')
def handle_connect(auth):
    token = auth.get('token')
    profile_id = auth.get('profile_id')
    if token in token_to_profile:
        p, time = token_to_profile.pop(token)
        if p == profile_id and datetime.now() < time + timedelta(minutes = 1):
            session_to_profile[request.sid] = profile_id
            print('Client connected', request.sid)
        else:
            print('Bad or expired token')
            return False
    else:
        print('Bad token')
        return False

@socketio.on('create-room')
def create_room(room_name):
    print('create_room', room_name)
    join_code = util.random_id(5)
    with DB_Connector() as db:
        while not db.add_room(join_code, room_name):
            continue
    print('create room success', join_code, room_name)
    return join_code

@socketio.on('join-room')    
def join_room(join_code):
    print('join-room', join_code)

    profile_id = session_to_profile[request.sid]

    with DB_Connector() as db:
        room_id = db.get_room_id(join_code)
        d = db.get_user_from_room_profile(room_id, profile_id)

        if d:
            user_data = db.compile_user_data(d)

        else:
            u = db.get_username(profile_id)
            x = db.add_user(room_id, profile_id)
            emit('update_user_data', {
                'profile_id': profile_id, 
                'rooms': util.stringifyTimes(db.get_profile_rooms(profile_id), 'creation_time')
                })

            user_data = {
                'username': u, 'user_id': x,
                'cash': 0, 'position': 0,
                'orders': [], 'trades': []
            }

        # TODO: is there a way to only keep certain keys of these 2 dicts?
        bbo = db.get_bbo_history(room_id)
        ld = db.get_room_trades(room_id)
        
    session_to_user[request.sid] = (user_data['user_id'], room_id)
    user_to_sessions.setdefault(user_data['user_id'], set()).add(request.sid)
    room_to_sessions.setdefault(room_id, set()).add(request.sid)

    return {
        'room_id': room_id, 
        'user_data': user_data,
        'bbo_history': util.stringifyTimes(bbo, 'bbo_time'),
        'ld_history': util.stringifyTimes(ld, 'creation_time'),
        'order_book': get_order_book(room_id)
        }

@socketio.on('exit-room')
def exit_room():
    user_id, room_id = session_to_user.pop(request.sid)
    user_to_sessions[user_id].remove(request.sid)
    room_to_sessions[room_id].remove(request.sid)
    print('exit_room', user_id, room_id)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in session_to_user:
        exit_room()
    p = session_to_profile.pop(request.sid)
    print('Client disconnected', p)

# TODO: NEEEDS TO BE DELETED BEFORE PUSHING TO PROD
@app.route('/sessions/<room_id>/<user_id>')
def get_sessions(room_id, user_id):
    room = rooms[room_id]
    users = room.users
    return list(users[user_id].sid)

@socketio.on('buy')
def buy(limit, quantity):
    buyer_id, room_id = session_to_user[request.sid]
    limit = int(limit)
    quantity = int(quantity)

    users_to_update = { buyer_id }
    orderbook_updates = []
    lastdone_updates = []

    with DB_Connector() as db:

        best_ask = db.get_best_ask(room_id)
        while best_ask and best_ask['limit_price'] <= limit and quantity > 0:
            seller_id = best_ask['user_id']
            volume = min(best_ask['quantity'], quantity)
            lastdone_updates.append(db.settle_trade(volume, best_ask['limit_price'], room_id, buyer_id, seller_id, True))
            orderbook_updates.append({'side': False, 'limit': best_ask['limit_price'], 'quantity': -volume})

            quantity -= volume
            if best_ask['quantity'] == volume:
                db.delete_order('S', best_ask['id'], seller_id)
            else:
                db.update_ask_quantity(best_ask['id'], -volume)
            
            users_to_update.add(seller_id)

            best_ask = db.get_best_ask(room_id)

        if quantity > 0:
            db.add_bid(buyer_id, room_id, limit, quantity)
            orderbook_updates.append({'side': True, 'limit': int(limit), 'quantity': quantity})

        for trade_id in lastdone_updates:
            emit_set('update_ld_history', 
            util.stringifyTime(db.get_trade_by_id(trade_id), 'creation_time'), 
            room_to_sessions[room_id])
        
        for user_id in users_to_update:
            emit_set('update_roomuser_data', db.compile_user_data(user_id), user_to_sessions[user_id])
        
    for order in orderbook_updates:
        emit_set('update_order_book', order, room_to_sessions[room_id])

    track_and_emit_bbo(room_id)

    return "Success"

@socketio.on('sell')
def sell(limit, quantity):
    seller_id, room_id = session_to_user[request.sid]
    limit = int(limit)
    quantity = int(quantity)

    users_to_update = { seller_id }
    orderbook_updates = []
    lastdone_updates = []

    with DB_Connector() as db:

        best_bid = db.get_best_bid(room_id)
        while best_bid and best_bid['limit_price'] >= limit and quantity > 0:
            buyer_id = best_bid['user_id']
            volume = min(best_bid['quantity'], quantity)
            lastdone_updates.append(db.settle_trade(volume, best_bid['limit_price'], room_id, buyer_id, seller_id, False))
            orderbook_updates.append({'side': True, 'limit': best_bid['limit_price'], 'quantity': -volume})

            quantity -= volume
            if best_bid['quantity'] == volume:
                db.delete_order('B', best_bid['id'], seller_id)
            else:
                db.update_ask_quantity(best_bid['id'], -volume)
            
            users_to_update.add(buyer_id)

            best_bid = db.get_best_bid(room_id)

        if quantity > 0:
            db.add_ask(seller_id, room_id, limit, quantity)
            orderbook_updates.append({'side': False, 'limit': int(limit), 'quantity': quantity})

        for trade_id in lastdone_updates:
            emit_set('update_ld_history', 
            util.stringifyTime(db.get_trade_by_id(trade_id), 'creation_time'), 
            room_to_sessions[room_id])
        
        for user_id in users_to_update:
            emit_set('update_roomuser_data', db.compile_user_data(user_id), user_to_sessions[user_id])
        
    for order in orderbook_updates:
        emit_set('update_order_book', order, room_to_sessions[room_id])

    track_and_emit_bbo(room_id)

    return "Success"

@socketio.on('delete')
def delete_order(order_side, order_id):
    user_id, room_id = session_to_user[request.sid]
    with DB_Connector() as db:
        order = db.get_order_by_id(order_side, order_id)
        db.delete_order(order_side, order_id, user_id)
        emit_set('update_roomuser_data', db.compile_user_data(user_id), user_to_sessions[user_id])
        emit_set('update_order_book', 
        {'side': order_side == 'B', 'limit': order['limit_price'], 'quantity': -order['quantity']}, 
        room_to_sessions[room_id])

    track_and_emit_bbo(room_id)

def track_and_emit_bbo(room_id):
    with DB_Connector() as db:
        old_bbo = db.get_latest_bbo_history(room_id)
        b, o = db.get_bbo_from_orders(room_id)
        cb, co = b if b else 0, o if o else 100
        if not old_bbo or (old_bbo['best_bid'], old_bbo['best_offer']) != (cb, co): # bbo is empty or bbo has changed:
            db.add_bbo_history(room_id, cb, co)
            emit_set(
                'update_bbo_history', 
                util.stringifyTime(db.get_latest_bbo_history(room_id), 'bbo_time'), 
                room_to_sessions[room_id])


@app.route('/order-book/<room_id>')
def get_order_book(room_id):
    bfreq = {}
    afreq = {}
    with DB_Connector() as db:
        for bid in db.get_room_bids(room_id):
            bfreq[bid['limit_price']] = bfreq.get(bid['limit_price'], 0) + bid['quantity']
        for ask in db.get_room_asks(room_id):
            afreq[ask['limit_price']] = afreq.get(ask['limit_price'], 0) + ask['quantity']

    d = {'bids': bfreq, 'asks': afreq}
    return d

@app.route('/all-player-stats/<room_id>')
def get_all_player_stats(room_id):
    room = rooms[room_id]
    users = room.users
    return [{
        'username': user.username,
        'cash': user.cash,
        'position': user.position
    } for user in room.users.values()]

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
