from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
from datetime import date, timedelta
import calendar

def generate_dates(start, end, frequency):
    """
    Retourne une liste de dates entre `start` et `end` selon une fréquence.

    Args:
        start (datetime): Date de début.
        end (datetime): Date de fin.
        frequency (str): 'jour', 'semaine' ou 'mois'.

    Returns:
        list[datetime]: Dates générées selon la fréquence.
    """

    freq_map = {
        'jour': DAILY,
        'semaine': WEEKLY,
        'mois': MONTHLY
    }

    return list(rrule(freq_map[frequency], dtstart=start, until=end))



def is_last_weekday_of_month(d):
    """Retourne True si la date `d` est le dernier jour de semaine de ce type dans son mois"""
    next_week = d + timedelta(days=7)
    return next_week.month != d.month and next_week.weekday() == d.weekday()

def get_nth_weekday_of_month(year, month, weekday, n):
    """Retourne la date du n-ième `weekday` dans un mois donné (si elle existe)"""
    count = 0
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        current = date(year, month, day)
        if current.weekday() == weekday:
            count += 1
            if count == n:
                return current
    return None

def get_last_weekday_of_month(year, month, weekday):
    """Retourne la date du dernier `weekday` dans un mois donné"""
    last_day = calendar.monthrange(year, month)[1]
    for day in range(last_day, 0, -1):
        current = date(year, month, day)
        if current.weekday() == weekday:
            return current
    return None

def get_weekday_occurrence(d):
    """Retourne combien de fois ce jour de semaine est déjà apparu dans le mois"""
    return ((d.day - 1) // 7) + 1

def generate_smart_weekday_recurrence(start_date, months=12):
    weekday = start_date.weekday()  # 0=lundi, ..., 6=dimanche
    recurrence = []
    is_last = is_last_weekday_of_month(start_date)
    nth = get_weekday_occurrence(start_date)

    for i in range(months):
        target_month = (start_date.month + i - 1) % 12 + 1
        target_year = start_date.year + (start_date.month + i - 1) // 12

        if is_last:
            recur_date = get_last_weekday_of_month(target_year, target_month, weekday)
        else:
            recur_date = get_nth_weekday_of_month(target_year, target_month, weekday, nth)

        if recur_date:
            recurrence.append(recur_date)

    return recurrence
