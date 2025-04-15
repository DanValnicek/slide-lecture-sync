from datetime import timedelta


def ms_to_hms(time_ms):
    return str(timedelta(milliseconds=time_ms)).split('.')[0]


def hms_to_ms(hms):
    """Convert HH:MM:SS.mmm format to milliseconds."""
    h, m, s = map(float, hms.split(":"))
    return int((h * 3600 + m * 60 + s) * 1000)
