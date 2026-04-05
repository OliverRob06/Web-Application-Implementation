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
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'Missing credentials'}), 401

        # Expect format: "Bearer adminkey"
        try:
            scheme, token = auth_header.split()
        except ValueError:
            return jsonify({'error': 'Invalid auth format'}), 401

        if scheme.lower() != 'bearer':
            return jsonify({'error': 'Invalid auth scheme'}), 401

        if not check_string(token, ADMIN_PASSWD):
            return jsonify({'error': 'Invalid admin token'}), 403

        return f(*args, **kwargs)

    return decorated_function