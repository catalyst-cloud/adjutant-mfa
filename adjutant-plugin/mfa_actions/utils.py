from datetime import datetime
from calendar import timegm

import six
import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.twofactor.totp import TOTP
from cryptography.hazmat.primitives.hashes import SHA1


def generate_totp_passcode(secret):
    """Generate TOTP passcode.
    :param bytes secret: A base32 encoded secret for TOTP authentication
    :returns: totp passcode as bytes
    """
    if isinstance(secret, six.text_type):
        secret = secret.encode('utf-8')

    while len(secret) % 8 != 0:
        secret = secret + b'='

    decoded = base64.b32decode(secret)
    totp = TOTP(
        decoded, 6, SHA1(), 30, backend=default_backend())
    return totp.generate(timegm(datetime.utcnow().utctimetuple())).decode()
