import configparser
import subprocess

from dateutil.parser import isoparse
from dateutil import tz

settings = configparser.ConfigParser(interpolation=None)
settings.read('./settings.ini')
local_tz = tz.gettz()


def create_next_message():
    try:
        shul_cal_url = settings.get('Recurring', 'calendar')
    except configparser.Error as e:
        print(e)
        return

    command = [
        "curl", "-s", shul_cal_url,
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    ]

    # Requests gets a 406, so we need a direct CURL command
    # The curl_cffi library works, but is also very shady
    shul_calendar = subprocess.run(command, capture_output=True, text=True, check=True).stdout

    summaries = set()
    all_days = []
    one_day = {}
    for line in shul_calendar.splitlines():
        line_data = line.split(':')
        if line_data[0] == 'SUMMARY':
            summaries.add(line_data[1])
            match line_data[1]:
                case 'Selichos/Shacharis':
                    one_day['event'] = 'Selichos'
                case 'Shacharis followed by Kinnos':
                    one_day['event'] = 'Shacharis'
                case 'Plag Mincha/Kabbolas Shabbos' | 'Early Mincha' | 'Mincha/Maariv' | 'Zman Mincha' | 'Zman Mincha/Kabbolas Shabbos':
                    one_day['event'] = 'Mincha'
                case 'Maariv followed by Eicha' | 'Maariv followed by Megillah':
                    one_day['event'] = 'Maariv'
                case 'Kol Nidre':
                    one_day['event'] = 'KolNidre'
                case 'Earliest Talis/Tefilin':
                    one_day['event'] = 'Tallis'
                case _:
                    one_day['event'] = line_data[1]
        elif line_data[0] == 'DTSTART':
            one_day['time'] = isoparse(line_data[1]).astimezone(local_tz).strftime("%B %d, %Y, %I:%M %p")
        elif line_data[0] == 'END':
            if one_day != {} and one_day['event'] in ('Shacharis', 'Selichos', 'Tallis', 'KolNidre', 'Maariv', 'Mincha', 'Megillah'): # Machatzis HaShekel
                print(one_day)
                all_days.append(one_day)
            one_day = {}

    event_set = set()
    for day in all_days:
        if day != {}:
            event_set.add(day['event'])

    for event in event_set:
        print(event)
