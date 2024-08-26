import util

class Room:
    def __init__(self, room_name):
        self.room_name = room_name
        self.room_id = util.random_id(5)

        self.users = {} # All Users belonging to the room {user_id: User}
        self.sessions = {} # All sessions currently active in this room {sid: user_id}

        self.bids = []
        self.asks = []
        self.trades = []

        self.last_buy_t = []
        self.last_buy_p = []
        self.last_sell_t = []
        self.last_sell_p = []

        self.best_bid_t = []
        self.best_bid_p = []
        self.best_offer_t = []
        self.best_offer_p = []

        self.bt, self.bp, self.ot, self.op = [], [], [], []

        self.lb_broadcast_i = 0
        self.ls_broadcast_i = 0
        self.bbo_broadcast_i = 0
