from enum import Enum
import os


class DBINFO:
    host = "some.url"
    user = os.getenv('DB_USER', '')
    password = os.getenv('DB_PASSWORD', '')
    database = "web_therapy"


class CONSTANTS:
    key = os.getenv('JWT_KEY', '')
    min_password_len = 8
    database_info = DBINFO
    auth_cookie_expiration = 30 * 24 * 60 * 60  # 30 days
    app_id = os.getenv('APP_ID', 'someidhere')
    video_folder = os.path.join('.', 'videos')
    thumbnail_folder = os.path.join('.', 'thumbs')

    debug = True
