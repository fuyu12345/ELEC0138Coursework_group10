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
    """
    Decorator to check if a token is present in the request header
    and if it is valid  
    """
    @wraps(f)
    def decorator(*args, **kwargs):
        token = session.get("token")

        if not token:
            return redirect(url_for('login'))

        try:
            token_payload = decode_auth_token(token)
            session['user_id'] = token_payload["sub"]
        except TokenValidationError as e:
            session.pop('user_id', None)
            session.pop('token', None)
            return redirect(url_for('login'))

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
    """
    Decodes the auth token
    :param auth_token:
    :return: integer|string
    """
    try:
        payload = jwt.decode(auth_token, app.config.get("SECRET_KEY"), algorithms=["HS256"])
        return payload
    except (ExpiredSignatureError, InvalidTokenError) as e:
        raise TokenValidationError("Invalid token. Please log in again.")