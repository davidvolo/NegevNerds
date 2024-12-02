import json

class ServiceLayer:
    def __init__(self, business_class):
        self.business_class = business_class

    def register(self, email, password, first_name, last_name):
        """Handle user registration and return JSON."""
        try:
            result = self.business_class.register(email, password, first_name, last_name)
            
            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def login(self, email, password):
        """Handle user login and return JSON."""
        try:
            result = self.business_class.login(email, password)
            
            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def logout(self, email):
        """Handle user logout and return JSON."""
        try:
            result = self.business_class.logout(email)
            
            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
