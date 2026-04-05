from functools import wraps
from flask import request, jsonify, session
import os
import hmac

#ADMIN PLACEHOLDER PASSWORD
ADMIN_PASSWD = os.environ.get("ADMIN_PASSWD", "adminkey")


def check_string(input_string, target_string):
    # more secure comparison
    return hmac.compare_digest(input_string, target_string)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') == 'admin':
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