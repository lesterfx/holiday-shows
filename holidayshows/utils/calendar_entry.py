from datetime import date, datetime, timedelta
from itertools import count

class CalendarEntry(object):
    def __init__(self, entry):
        today = date.today()

        self.start = datetime.strptime(entry['start'], '%B %d').date().replace(year=today.year)
        self.end = datetime.strptime(entry['end'], '%B %d').date().replace(year=today.year)

        self.days = frozenset(entry.get('days', []))
        self.animation = frozenset(entry['animation'])
        
        self.name = entry['name']

    def __repr__(self):
        return self.name

    def iter(self):
        today = date.today()
        if self.end < self.start:
            # crosses december 31, so end next year instead of this year
            extrayear = 1
        else:
            extrayear = 0
        for year in count(today.year):
            start = self.start.replace(year=year)
            end = self.end.replace(year=year+extrayear)
            day = start
            if day < today:
                day = today
            while day <= end:
                if self.days:
                    weekday = day.strftime('%A')
                    if weekday in self.days:
                        # print(f'{self.name} next show is {day}')
                        yield day
                    # else:
                        # print(f'{self.name} on {day}: {weekday} not in {list(self.days)}')
                else:
                    # print(f'{self.name} next show is {day}')
                    yield day
                day += timedelta(1)
