from datetime import datetime
from calendar import monthrange
from time import time as time_orig

# now = current time as datetime object
# time = current time as timestamp
# offset = UTC timezone offset in seconds
now = datetime.now
def time_int(): return int(time_orig())
offset = now().astimezone().tzinfo.utcoffset(None).seconds

MINUTE = 60
HOUR = 60*60
DAY = 24*60*60
WEEK = 7*24*60*60
timertypes = ("Daily", "Weekly", "Weekday", "Monthly", "Custom", "Once")
weekdays = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
time_measurements = ("days", "hours", "minutes")  # , "seconds")


class TimerTemplate:
    # not for use, only inheritance
    def __init__(self, comment, lastclicked, extraargs):
        self.lastclicked = lastclicked
        self.comment = comment
        self.extraargs = extraargs
        self.starttime = None
        self.interval = None
    
    def lastdeadline(self):
        intervalspassed = (time_int() - self.starttime) // self.interval
        lasttimestamp = self.starttime + self.interval * intervalspassed
        return lasttimestamp
    
    def nextdeadline(self):
        return self.lastdeadline() + self.interval

    def remaining_delta(self):
        return self.nextdeadline() - time_int()
    
    def remaining_str(self):
        timeleft = self.remaining_delta()
        minutesleft = (timeleft//MINUTE) % 60
        hoursleft = (timeleft//HOUR) % 24
        daysleft = timeleft//DAY
        if daysleft:
            return f"{daysleft}d {hoursleft}h"
        elif hoursleft:
            return f"{hoursleft}h {minutesleft:02}m"
        elif minutesleft:
            return f"{minutesleft}m"
        else:
            return "Less than 1m"


class CustomTimer(TimerTemplate):
    def __init__(self, comment, lastclicked, extraargs):
        super().__init__(comment, lastclicked, extraargs)

        # extraargs = (start time, integer, interval measurement units)
        self.starttime, interval_value, interval_units = extraargs

        match interval_units:
            case "days":
                self.interval = interval_value * DAY
            case "hours":
                self.interval = interval_value * HOUR
            case "minutes":
                self.interval = interval_value * MINUTE
            case "seconds":
                self.interval = interval_value


class OnceTimer(TimerTemplate):
    def __init__(self, comment, lastclicked, extraargs):
        super().__init__(comment, lastclicked, extraargs)

        # extraargs = (start time)
        self.starttime = extraargs[0]

    def lastdeadline(self):
        return self.starttime

    def nextdeadline(self):
        return self.starttime

    def remaining_delta(self):
        return max(0, self.nextdeadline() - time_int())

    def remaining_str(self):
        if self.remaining_delta() == 0:
            return "Overdue"
        else:
            return super().remaining_str()
    

class DailyTimer(TimerTemplate):
    def __init__(self, comment, lastclicked, extraargs):
        super().__init__(comment, lastclicked, extraargs)
        # extraargs = (hours, minutes)
        
        self.starttime = time_int() - (time_int() % DAY) - offset - DAY
        self.starttime += self.extraargs[0]*HOUR + self.extraargs[1]*MINUTE
        
        self.interval = DAY


class WeeklyTimer(TimerTemplate):
    def __init__(self, comment, lastclicked, extraargs):
        super().__init__(comment, lastclicked, extraargs)
        # extraargs = (day of week, hours, minutes)
        
        self.starttime = time_int() - (time_int() % WEEK) - offset - WEEK - DAY*3
        self.starttime += self.extraargs[0]*DAY + self.extraargs[1]*HOUR + self.extraargs[2]*MINUTE
        
        self.interval = WEEK


class WeekdayTimer(TimerTemplate):
    def __init__(self, comment, lastclicked, extraargs):
        super().__init__(comment, lastclicked, extraargs)
        # extraargs = ((days of week), hours, minutes)
        
        self.starttime = time_int() - (time_int() % WEEK) - offset - WEEK - DAY*3
        self.starttime += self.extraargs[1]*HOUR + self.extraargs[2]*MINUTE
        
        self.interval = WEEK

    def __gettimers(self):
        weekstimes = []
        for entry in self.extraargs[0]:
            temp_starttime = self.starttime + entry * DAY
            intervalspassed = (time_int() - temp_starttime) // self.interval
            lasttimestamp = temp_starttime + self.interval * intervalspassed
            weekstimes.append(lasttimestamp)
        return weekstimes

    def lastdeadline(self):
        return max(self.__gettimers())
    
    def nextdeadline(self):
        return min(self.__gettimers()) + self.interval


class MonthlyTimer(TimerTemplate):
    def __init__(self, comment, lastclicked, extraargs):
        super().__init__(comment, lastclicked, extraargs)
        # extraargs = (day, hours, minutes)

    def __gettimers(self):
        temptime1 = now()

        # get current month's day by variable, get last day of month if variable is out of bounds
        temptime2 = datetime(
            temptime1.year,
            temptime1.month,
            min(monthrange(temptime1.year, temptime1.month)[1], self.extraargs[0]),
            self.extraargs[1],
            self.extraargs[2])

        if temptime1 > temptime2:
            monthdelta = 1
        else:
            monthdelta = -1

        newyear = (temptime1.year*12+temptime1.month+monthdelta)//12
        newmonth = (12+temptime1.month+monthdelta) % 12

        # get previous or next month's day by variable, get last day of month if variable is out of bounds
        temptime3 = datetime(
            newyear,
            newmonth,
            min(monthrange(newyear, newmonth)[1], self.extraargs[0]),
            self.extraargs[1],
            self.extraargs[2])

        return temptime2, temptime3

    def lastdeadline(self):
        return int(datetime.timestamp(min(self.__gettimers())))
    
    def nextdeadline(self):
        return int(datetime.timestamp(max(self.__gettimers())))
