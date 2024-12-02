class User:
    def __init__(self, id, email, password, first_name, last_name):
        self.id = id
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.loggedIn = False
    
    def login(self):
        self.loggedIn = True
    
    def logout(self):
        self.loggedIn = False
