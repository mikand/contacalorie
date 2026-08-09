import os.path

from functools import wraps
from flask import Response, request
from werkzeug.security import check_password_hash, generate_password_hash

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.txt")

def check_auth(username, password):
    """Check a username/password pair against users.txt.

    Each line is `username:hash`, where the hash comes from
    `python utils.py <username>`. check_password_hash compares in constant
    time, so a wrong password leaks nothing through timing.
    """
    with open(USERS_FILE) as f:
        for line in f:
            name, _, stored = line.strip().partition(':')
            if name == username and stored:
                return check_password_hash(stored, password)
    return False

def is_cleartext():
    """True only when we positively know the request arrived over plain HTTP.

    ponytail: trusts the reverse proxy's X-Forwarded-Proto and stays silent
    when the header is absent, so a proxy that does not set it cannot lock
    everyone out. Tighten to `!= 'https'` once the header is confirmed
    present in production.
    """
    forwarded = request.headers.get('X-Forwarded-Proto')
    local = request.host.split(':')[0] in ('localhost', '127.0.0.1')
    return forwarded == 'http' and not local

def authenticate():
    """Sends a 401 response that enables basic auth.

    The body reaches a browser, so it is Italian like every other response.
    """
    return Response(
    'Credenziali non valide o mancanti.\n'
    'Accedi con nome utente e password.', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if is_cleartext():
            # Never invite Basic Auth credentials onto an unencrypted channel.
            return Response('HTTPS richiesto.', 403)
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

if __name__ == '__main__':
    # Generate a users.txt line: python utils.py <username>
    import getpass
    import sys

    if len(sys.argv) != 2:
        sys.exit("usage: python utils.py <username>")
    print("%s:%s" % (sys.argv[1], generate_password_hash(getpass.getpass("password: "))))
