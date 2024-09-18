import os
import pymysql
from datetime import datetime
import util

class DB_Connector:
    def __init__(self):
        self.connection = pymysql.connect(
            host=os.environ.get('DATABASE_IP', 'localhost'), 
            user=os.environ.get('DATABASE_USR', 'root'), 
            password=os.environ.get('DATABASE_PW'), 
            db=os.environ.get('DATABASE_NAME', 'live_order_book_db'), 
            cursorclass=pymysql.cursors.DictCursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def add_profile(self, username, salt, sha):
        with self.connection.cursor() as cursor:
            try:
                sql = "INSERT INTO profiles (username, salt, sha) VALUES (%s, %s, %s);"
                cursor.execute(sql, (username, salt, sha))
                profile_id = cursor.lastrowid
                self.connection.commit()
            except Exception as e:
                print(e)
        return profile_id

    def get_profile(self, username):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM profiles WHERE username = %s LIMIT 1;"
            cursor.execute(sql, (username))
            d = cursor.fetchone()
        return d

    def get_profile_rooms(self, profile_id):
        with self.connection.cursor() as cursor:
            sql = ("SELECT rooms.id, rooms.creation_time, rooms.join_code, rooms.room_name "
            "FROM rooms INNER JOIN users "
            "ON rooms.id = users.room_id AND users.profile_id = %s;")
            cursor.execute(sql, (profile_id))
            a = cursor.fetchall()
        return a

    def add_room(self, join_code, room_name):
        status = False
        with self.connection.cursor() as cursor:
            try:
                sql = "INSERT INTO rooms (join_code, room_name) VALUES (%s, %s);"
                cursor.execute(sql, (join_code, room_name))
                self.connection.commit()
                status = True
            except Exception as e:
                print(e)
        return status

    def get_room_id(self, join_code):
        with self.connection.cursor() as cursor:
            sql = "SELECT id FROM rooms WHERE join_code = %s LIMIT 1;"
            if cursor.execute(sql, (join_code)):
                d = cursor.fetchone()
        return d['id']

    def add_user(self, room_id, profile_id):
        with self.connection.cursor() as cursor:
            try:
                sql = "INSERT INTO users (profile_id, room_id) VALUES (%s, %s);"
                cursor.execute(sql, (profile_id, room_id))
                user_id = cursor.lastrowid
                self.connection.commit()
            except Exception as e:
                print(e)
        return user_id

    def get_user_from_id(self, user_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE id = %s LIMIT 1;"
            cursor.execute(sql, (user_id))
            d = cursor.fetchone()
        return d

    def get_user_from_room_profile(self, room_id, profile_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM users WHERE room_id = %s AND profile_id = %s LIMIT 1;"
            cursor.execute(sql, (room_id, profile_id))
            d = cursor.fetchone()
        return d

    def get_username(self, profile_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT username FROM profiles WHERE id = %s LIMIT 1;"
            cursor.execute(sql, (profile_id))
            d = cursor.fetchone()
        return d.get('username')

    def get_user_orders(self, user_id):
        with self.connection.cursor() as cursor:
            bids_sql = "SELECT * FROM bids WHERE user_id = %s;"
            cursor.execute(bids_sql, (user_id))
            bids = cursor.fetchall()
            asks_sql = "SELECT * FROM asks WHERE user_id = %s;"
            cursor.execute(asks_sql, (user_id))
            asks = cursor.fetchall()
        return list(bids) + list(asks)

    def get_user_trades(self, user_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM trades WHERE buyer_id = %s OR seller_id = %s;"
            cursor.execute(sql, (user_id, user_id))
            trades = cursor.fetchall()
        return trades

    def settle_trade(self, volume, price, room_id, buyer_id, seller_id, buy_aggr):
        with self.connection.cursor() as cursor:
            try: 
                trade_sql = ("INSERT INTO trades (volume, price, room_id, buyer_id, seller_id, buy_aggr) "
                "VALUES (%s,%s,%s,%s,%s,%s);")
                cursor.execute(trade_sql, (volume, price, room_id, buyer_id, seller_id, buy_aggr))
                trade_id = cursor.lastrowid
                buyer_sql = "UPDATE users SET cash = cash - %s, position = position + %s WHERE id = %s;"
                cursor.execute(buyer_sql, (volume * price, volume, buyer_id))
                seller_sql = "UPDATE users SET cash = cash + %s, position = position - %s WHERE id = %s;"
                cursor.execute(seller_sql, (volume * price, volume, seller_id))
                
                self.connection.commit()
            except Exception as e:
                print(e)

        return trade_id

    def update_bid_quantity(self, order_id, dQuantity):
        with self.connection.cursor() as cursor:
            try:
                sql = "UPDATE bids SET quantity = quantity + %s WHERE id = %s;"
                cursor.execute(sql, (dQuantity, order_id))
                self.connection.commit()
            except Exception as e:
                print(e)

    def update_ask_quantity(self, order_id, dQuantity):
        with self.connection.cursor() as cursor:
            try:
                sql = "UPDATE asks SET quantity = quantity + %s WHERE id = %s;"
                cursor.execute(sql, (dQuantity, order_id))
                self.connection.commit()
            except Exception as e:
                print(e)

    def add_bbo_history(self, room_id, best_bid, best_offer):
        with self.connection.cursor() as cursor:
            sql = ("INSERT INTO bbohistory (room_id, best_bid, best_offer) "
            "VALUES (%s,%s,%s);")
            cursor.execute(sql, (room_id, best_bid, best_offer))
            self.connection.commit()

    def bbo_history_is_empty(self, room_id):
        empty = True
        with self.connection.cursor() as cursor:
            sql = "SELECT id FROM bbohistory WHERE room_id = %s LIMIT 1;"
            if cursor.execute(sql, (room_id)):
                empty = False
        return empty

    def get_bbo_history(self, room_id, since_time=datetime.fromtimestamp(0)):
        with self.connection.cursor() as cursor:
            sql = ("SELECT bbo_time, best_bid, best_offer FROM bbohistory "
            "WHERE room_id = %s AND bbo_time > %s ORDER BY bbo_time ASC;")
            cursor.execute(sql, (room_id, since_time))
            a = cursor.fetchall()
        return a

    def get_latest_bbo_history(self, room_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM bbohistory WHERE room_id = %s ORDER BY bbo_time DESC LIMIT 1;"
            cursor.execute(sql, (room_id))
            d = cursor.fetchone()
        return d

    def get_bbo_from_orders(self, room_id):
        with self.connection.cursor() as cursor:
            bb_sql = "SELECT limit_price FROM bids WHERE room_id = %s ORDER BY limit_price DESC, creation_time ASC LIMIT 1;"
            cursor.execute(bb_sql, (room_id))
            d = cursor.fetchone()
            bb = d['limit_price'] if d else None
            bo_sql = "SELECT limit_price FROM asks WHERE room_id = %s ORDER BY limit_price ASC, creation_time ASC LIMIT 1;"
            cursor.execute(bo_sql, (room_id))
            d = cursor.fetchone()
            bo = d['limit_price'] if d else None
            return (bb, bo)

    def get_best_bid(self, room_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM bids WHERE room_id = %s ORDER BY limit_price DESC, creation_time ASC LIMIT 1;"
            cursor.execute(sql, (room_id))
            d = cursor.fetchone()
        return d

    def get_best_ask(self, room_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM asks WHERE room_id = %s ORDER BY limit_price ASC, creation_time ASC LIMIT 1;"
            cursor.execute(sql, (room_id))
            d = cursor.fetchone()
        return d

    def add_bid(self, user_id, room_id, limit_price, quantity):
        status = False
        with self.connection.cursor() as cursor:
            try:
                sql = "INSERT INTO bids (user_id, room_id, limit_price, quantity) VALUES (%s,%s,%s,%s);"
                cursor.execute(sql, (user_id, room_id, limit_price, quantity))
                self.connection.commit()
                status = True
            except Exception as e:
                print(e)
        return status

    def add_ask(self, user_id, room_id, limit_price, quantity):
        status = False
        with self.connection.cursor() as cursor:
            try:
                sql = "INSERT INTO asks (user_id, room_id, limit_price, quantity) VALUES (%s,%s,%s,%s);"
                cursor.execute(sql, (user_id, room_id, limit_price, quantity))
                self.connection.commit()
                status = True
            except Exception as e:
                print(e)
        return status

    def delete_order(self, order_side, order_id, user_id):
        status = False
        with self.connection.cursor() as cursor:
            try:
                if order_side == 'B':
                    typestring = 'bids'
                elif order_side == 'S':
                    typestring = 'asks'
                else:
                    return False
                
                sql = f"DELETE FROM {typestring} WHERE id = %s AND user_id = %s LIMIT 1;"
                if cursor.execute(sql, (order_id, user_id)):
                    self.connection.commit()
                    status = True
            except Exception as e:
                print(e)
        return status

    def get_order_by_id(self, order_side, order_id):
        with self.connection.cursor() as cursor:
            if order_side == 'B':
                typestring = 'bids'
            elif order_side == 'S':
                typestring = 'asks'
            else:
                return False

            sql = f"SELECT * FROM {typestring} WHERE id = %s;"
            cursor.execute(sql, (order_id))
            d = cursor.fetchone()
        return d

    def get_room_bids(self, room_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM bids WHERE room_id = %s;"
            cursor.execute(sql, (room_id))
            a = cursor.fetchall()
        return a

    def get_room_asks(self, room_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM asks WHERE room_id = %s;"
            cursor.execute(sql, (room_id))
            a = cursor.fetchall()
        return a

    def get_room_trades(self, room_id, since_time=datetime.fromtimestamp(0)):
        with self.connection.cursor() as cursor:
            sql = ("SELECT creation_time, volume, price, buy_aggr FROM trades "
            "WHERE room_id = %s AND creation_time > %s ORDER BY creation_time ASC;")
            cursor.execute(sql, (room_id, since_time))
            a = cursor.fetchall()
        return a

    def get_trade_by_id(self, trade_id):
        with self.connection.cursor() as cursor:
            sql = "SELECT creation_time, volume, price, buy_aggr FROM trades WHERE id = %s;"
            cursor.execute(sql, (trade_id))
            d = cursor.fetchone()
        return d

    def compile_user_data(self, d):
        if isinstance(d, int):
            d = self.get_user_from_id(d)

        username = self.get_username(d['profile_id'])
        orders = self.get_user_orders(d['id'])
        trades = self.get_user_trades(d['id'])

        return {
            'username': username, 
            'user_id': d['id'], 
            'cash': d['cash'], 
            'position': d['position'], 
            'orders': util.stringifyTimes(orders, 'creation_time'), 
            'trades': util.stringifyTimes(trades, 'creation_time')
        }

    def get_room_player_stats(self, room_id):
        pass