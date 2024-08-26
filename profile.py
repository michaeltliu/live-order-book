import util

class Profile:
    def __init__(self, username):
        self.username = username
        self.user_id = util.random_id()
        self.rooms = set() # Tracks all rooms that Profile belongs to {room_id} 