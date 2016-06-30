__author__ = 'jie'

import pytz
from tzlocal import get_localzone

def time_local(time_data):
    return time_data.replace(tzinfo=pytz.utc).astimezone(tz=get_localzone())

def time_format(time_data):
    if time_data is None:
        return None
    return time_local(time_data).strftime("%a, %H:%M, %d/%m/%Y")

def time_to_filename(time_data):
    return time_local(time_data).strftime("%Y-%m-%d_%H-%M-%S")
