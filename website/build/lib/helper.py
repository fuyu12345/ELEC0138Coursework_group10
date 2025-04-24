import datetime
from functools import wraps
import jwt
from flask import request, make_response, current_app as app
from src import db
from src.model import User
from flask import session
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from flask import redirect, url_for, render_template
def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        # First, try to get the token from the Authorization header
        token = request.headers.get("Authorization")
        # If not found, try to get it from the session
        if not token:
            token = session.get("token")
        
        if not token:
            response = {"message": "Authentication Token missing"}
            return make_response(response, 401)
        
        # Decode the token (assuming it's prefixed with "Bearer ", adjust if necessary)
        try:
            if token.startswith("Bearer "):
                token = token[7:]  # Remove "Bearer " prefix if present
            token_payload = decode_auth_token(token)
            
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError) as e:
            response = {"message": str(e)}
            render_template('login.html')

        # Additional user check logic as before...
        
        return f(*args, **kwargs)
    return decorator

def encode_auth_token(user_id):
    """Generates the Auth Token

    :param: string user_id  The user id of the user logging in
    :return: string
    """
    try:
        
        token = jwt.encode(
            # Sets the token to expire in 5 mins
            payload={
                "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5),
                "iat": datetime.datetime.now(datetime.UTC),
                "sub": user_id,
            },
            # Flask app secret key, matches the key used in the decode() in the decorator
            key=app.config['SECRET_KEY'],
            # Matches the algorithm in the decode() in the decorator
            algorithm='HS256'
        )
        return token
    except Exception as e:
        return e


class TokenValidationError(Exception):
    pass

def decode_auth_token(auth_token):
    try:
        payload = jwt.decode(auth_token, app.config.get("SECRET_KEY"), algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        return redirect(url_for('login'))
       
    except InvalidTokenError:
        raise TokenValidationError("Invalid token. Please log in again.")