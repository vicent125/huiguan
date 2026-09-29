from datetime import datetime, timedelta

def get_beijing_time():
    return datetime.utcnow() + timedelta(hours=8)
