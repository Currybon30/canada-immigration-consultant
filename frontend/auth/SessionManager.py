import requests

class SessionManager(requests.Session):
    def __init__(self):
        super().__init__()
    
    def get_session(self):
        return self