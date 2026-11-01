import configparser
import platform
import subprocess

from datetime import datetime, timedelta

import requests
from dateutil.parser import isoparse
from dateutil import tz

settings = configparser.ConfigParser(interpolation=None)
settings.read('./settings.ini')
local_tz = tz.gettz()

silent_yamim_tovim = [
    'Pesach I',
    'Pesach II',
    'Pesach VII',
    'Pesach VIII',
    'Rosh Hashana',
    'Rosh Hashana II',
    'Shavuot I',
    'Shavuot II',
    'Shmini Atzeret',
    'Simchat Torah',
    'Sukkot I',
    'Sukkot II',
    'Yom Kippur'
]


def get_calendar():
    try:
        shul_cal_url = settings.get('Recurring', 'calendar')
    except configparser.Error as e:
        print(e)
        return None

    command = [
        "curl", "-s", shul_cal_url,
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    ]

    # Requests gets a 406, so we need a direct CURL command
    # The curl_cffi library works, but is also very shady
    shul_calendar = subprocess.run(command, capture_output=True, text=True, check=True).stdout

    all_days = {}
    summary = dt = ''

    for line in shul_calendar.splitlines():
        line_data = line.split(':')
        if line_data[0] == 'SUMMARY':
            match line_data[1]:
                case 'Selichos/Shacharis':
                    summary = 'Selichos'
                case 'Shacharis followed by Kinnos':
                    summary = 'Shacharis'
                case 'Plag Mincha/Kabbolas Shabbos' | 'Early Mincha' | 'Mincha/Maariv' | 'Zman Mincha' | 'Zman Mincha/Kabbolas Shabbos':
                    summary = 'Mincha'
                case 'Maariv followed by Eicha' | 'Maariv followed by Megillah':
                    summary = 'Maariv'
                case 'Kol Nidre':
                    summary = 'KolNidre'
                case 'Earliest Talis/Tefilin':
                    summary = 'Tallis'
                case _:
                    summary = line_data[1]
        elif line_data[0] == 'DTSTART':
            dt = isoparse(line_data[1]).astimezone(local_tz) # .strftime("%B %d, %Y, %I:%M %p")
        elif line_data[0] == 'END':
            if dt != '' and summary in ('Shacharis', 'Selichos', 'Tallis', 'KolNidre', 'Maariv', 'Mincha', 'Megillah'): # Machatzis HaShekel
                all_days[dt] = summary
            summary = dt = ''

    # for dt, event in all_days.items():
    #     print(dt.strftime("%B %d, %Y, %I:%M %p") + ' => ' + event)

    return all_days

def get_yom_tov():
    r = requests.get(settings.get('Recurring', 'holidays'))

    yamim_tovim = {}
    summary = dt = ''
    for line in r.text.splitlines():
        line_data = line.split(':')
        if line_data[0] == 'SUMMARY':
            summary = line_data[1].split(' 57')[0]
        elif line_data[0] == 'DTSTART;VALUE=DATE':
            dt = datetime.strptime(line_data[1], "%Y%m%d").date()
        elif line_data[0] == 'END':
            if summary in silent_yamim_tovim:
                yamim_tovim[dt] = summary
            summary = dt = ''

    return yamim_tovim


def create_next_message(after = None):
    after = (after if after is not None else datetime.now()).astimezone(local_tz)

    calendar = get_calendar()
    if calendar is None:
        return ""

    next_entry = prev_entry = None
    for entry in calendar.items():
        if entry[0] > after:
            next_entry = entry
            break
        prev_entry = entry

    yamim_tovim = get_yom_tov()

    if next_entry[0].date() in yamim_tovim:
        if settings.get('Recurring', 'shabbos_mode') != 'N':
            return None
        settings.set('Recurring', 'shabbos_mode', 'Y')
        return "Good Yom Tov"
    elif next_entry[0].weekday() == 5:
        if settings.get('Recurring', 'shabbos_mode') != 'N':
            return None
        settings.set('Recurring', 'shabbos_mode', 'Y')
        if (next_entry[0] + timedelta(days=1)).date() in yamim_tovim:
            return "Good Yom Tov"
        return 'Good Shabbos'
    else:
        # End "shabbos_mode" 10 minutes after maariv
        if settings.get('Recurring', 'shabbos_mode') == 'Y':
            if (prev_entry[0] + timedelta(minutes=10)) < after:
                settings.set('Recurring', 'shabbos_mode', 'N')
                return build_message(next_entry)
            else:
                return None
        return build_message(next_entry)


def build_message(entry: tuple):
    # Rolling is okay
    clock_string = "%#I:%M%p" if platform.platform().startswith('Windows') else "%-I:%M%p"


    return f"{entry[1]} {entry[0].strftime(clock_string)}"
    # return f"{entry[1][:6]} {entry[0].strftime(clock_string)}" # for 13 character limit
