from datetime import datetime
import pytz


def get_timezone():
    # return datetime.now(pytz.timezone("America/Argentina/Buenos_Aires"))
    tz = pytz.timezone("America/Argentina/Buenos_Aires")
    return datetime.now(tz).astimezone(tz).replace(tzinfo=None)