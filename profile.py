import util
import hashlib

class Profile:
    def __init__(self, username, salt, sha):
        self.username = username
        self.salt = salt
        self.sha = sha
        self.user_id = util.random_id()
        self.rooms = set() # Tracks all rooms that Profile belongs to {room_id} 