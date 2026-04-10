from functools import wraps
from flask import request, jsonify
from test import tokens

#middleware to check api key
def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kkwargs):
        token = request.headers.get("Authorization")
        if not token or token not in tokens:
            return{"error":"unauthorised"}, 401
        
        request.user = tokens[token]

        
        #continue to the actual API route if key is valid
        return f(*args, **kkwargs)
    
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kkwargs):
        token = request.headers.get("Authorization")
        if not token or token not in tokens:
            return{"error":"unauthorised"}, 401
        
        user = tokens[token]

        if user["role" != "admin"]:
            return{"error": "not admin"}, 403
        #continue to the actual API route if key is valid
        return f(*args, **kkwargs)
    
    return decorated_function
