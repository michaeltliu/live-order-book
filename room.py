import util

class Room:
    def __init__(self, room_name):
        self.room_name = room_name #string
        self.room_id = util.random_id(5) #string

        self.users = {} # All Users belonging to the room {user_id: User}
        self.sessions = {} # All sessions currently active in this room {sid: user_id}

        self.bids = []
        self.asks = []
        self.trades = []

        ''' LAST DONES'''
        self.last_buy_t = [] # array of datetime strings ['datetime1', 'datetime2', ... ]
        self.last_buy_p = [] # array of ints [price1, price2, price3, ...]
        self.last_sell_t = [] # array of datetime strings ['datetime1', 'datetime2', ... ]
        self.last_sell_p = [] # array of ints [price1, price2, price3, ...]

        '''BEST BID/OFFER HISTORY (BBO HISTORY)'''
        self.best_bid_t = [] # array of datetime strings ['datetime1', 'datetime2', ... ]
        self.best_bid_p = [] # array of ints [price1, price2, price3, ...]
        self.best_offer_t = []
        self.best_offer_p = []

        self.bt, self.bp, self.ot, self.op = [], [], [], []

        self.lb_broadcast_i = 0
        self.ls_broadcast_i = 0
        self.bbo_broadcast_i = 0
