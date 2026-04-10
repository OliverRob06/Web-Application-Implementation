from functools import wraps
from flask import request, jsonify
from models import APIkey, db


def require_api_key(role = None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = request.headers.get("X-API-KEY")
            
            if not key:
                return jsonify({"error": "Invalid or Missing API key"}), 403
            
            key_entry = APIkey.query.filter_by(key=key).first()

            if not key_entry:
                return jsonify({"error":"Invalid API key"}), 403
            
            #role check
            
            if role and key_entry.role != role:
                return jsonify({"error": "Not have premission"}), 403
            
            key_entry.request_count +=1
            db.session.commit()

            return f(*args, **kwargs)
        return decorated_function
    return decorator

