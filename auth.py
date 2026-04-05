from functools import wraps
from flask import request, jsonify

#ADMIN PLACEHOLDER PASSWORD
ADMIN_PASSWD = 'adminkey'

def check_string(input_string, target_string):
    return input_string == target_string

def admin_required(f):
    @wraps(f)
    def decorated_functions(*args, **kwargs):
        user_password_string = request.headers.get('Authorization-Token')

        if not user_password_string:
            return jsonify({'error': 'Missing password'}), 401

        if not check_string(user_password_string, ADMIN_PASSWD):
            return {'error': 'Invalid admin string. Access Denied.'}, 403
        
        return f(*args, **kwargs)
    return decorated_functions