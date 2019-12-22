import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = "=&b_kf3=r@vd1!$7y9wz3g3ngqd=rtj19r!!me2pk^fh460q3)"

INSTALLED_APPS = ["test_app"]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}
