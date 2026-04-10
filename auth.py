from functools import wraps
from flask import request, jsonify
from models import APIkey, db


def require_api_key(role = None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = request.headers.get("X-API-KEY")
            
            if not key:
                return ({"error": "Invalid or Missing API key"}), 403
            
            key_entry = APIkey.query.filter_by(key=key).first()

            if not key_entry:
                return ({"error":"Invalid API key"}), 403
            
            #role check
            
            if role and key_entry.role != role:
                return ({"error": "Not have premission"}), 403
            
            key_entry.request_count +=1
            db.session.commit()

            return f(*args, **kwargs)
        
        auth_header = request.headers.get('Authorization')

        # if nothing entered in the password field
        if not auth_header:
            return jsonify({'error': 'Missing credentials'}), 401
        
        # if the password is wrong
        if not check_string(auth_header, ADMIN_PASSWD):
            return jsonify({'error': 'Invalid admin password'}), 403

        return f(*args, **kwargs)

    return decorated_function