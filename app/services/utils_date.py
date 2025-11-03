from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY
from datetime import date, timedelta, datetime, time
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
    """Retourne True si la date `d` est le dernier jour de semaine
     de ce type dans son mois"""
    next_week = d + timedelta(days=7)
    return next_week.month != d.month and next_week.weekday() == d.weekday()


def get_nth_weekday_of_month(year, month, weekday, n):
    """Retourne la date du n-ième `weekday` dans un
    mois donné (si elle existe)"""
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
    """Retourne combien de fois ce jour de
    semaine est déjà apparu dans le mois"""
    return ((d.day - 1) // 7) + 1


from datetime import datetime

def generate_smart_weekday_recurrence(start_date, end_date):
    """
    Génére une récurrence mensuelle intelligente (ex: 2e mardi de chaque mois)
    entre `start_date` et `end_date`, en conservant uniquement l'heure et les minutes.

    Args:
        start_date (datetime): Date/heure de début.
        end_date (datetime): Date/heure de fin.

    Returns:
        list[datetime]: Liste des datetimes générés.
    """
    weekday = start_date.weekday()
    is_last = is_last_weekday_of_month(start_date)
    nth = get_weekday_occurrence(start_date)

    recurrence = []

    current_year = start_date.year
    current_month = start_date.month

    # Extraire heure et minute depuis start_date
    hour = start_date.hour
    minute = start_date.minute

    while True:
        if datetime(current_year, current_month, 1) > end_date:
            break

        if is_last:
            base_date = get_last_weekday_of_month(current_year,
                                                  current_month, weekday)
        else:
            base_date = get_nth_weekday_of_month(current_year, 
                                                 current_month, weekday, nth)

        if base_date:
            date_part = base_date.isoformat()  # Ex: '2025-08-20'
            time_part = f"{hour:02}:{minute:02}"
            recur_date = datetime.fromisoformat(f"{date_part}T{time_part}")

            if start_date <= recur_date <= end_date:
                recurrence.append(recur_date)

        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    return recurrence



def generate_day_recurrence(start_date, end_date, weekday):
    """

    A COMPLETER FAUT AJOPTUER DES TRUCS DANS LE XML
    Génère toutes les dates correspondant à un jour de semaine fixe
    (comme tous les lundis) entre deux dates.

    Args:
        start_date (date): Date de début.
        end_date (date): Date de fin.
        weekday (int): Jour de semaine (0=lundi, ..., 6=dimanche)

    Returns:
        list[date]: Liste des dates correspondant à ce jour.
    """
    # Décale jusqu'au premier jour correspondant
    delta_days = (weekday - start_date.weekday()) % 7
    first_match = start_date + timedelta(days=delta_days)

    current = first_match
    recurrence = []

    while current <= end_date:
        recurrence.append(current)
        current += timedelta(weeks=1)

    return recurrence


def generate_multi_days_recurrence(start_date, end_date, weekday_names):
    """
    Génère toutes les dates correspondant à un ou plusieurs jours de semaine fixes (ex lundi, mardi..)

    Args:
        start_date (date): Date de début.
        end_date (date): Date de fin.
        weekday_names (list[int]): Jour de semaine (0=lundi, ..., 6=dimanche)

    Retourne une liste de datetimes entre start_date et end_date inclus si le jour est dans weekday_names.
    """
    mapping = {
        'lundi': 0, 'mardi': 1, 'mercredi': 2, 'jeudi': 3,
        'vendredi': 4, 'samedi': 5, 'dimanche': 6
    }
    weekdays = {mapping[w.lower()] for w in weekday_names if w and w.lower() in mapping}
    dates = []
    # normaliser début/fin en datetime (déjà fait en extract_form_data)
    cur = start_date
    # on parcourt jour par jour
    while cur <= end_date:
        if cur.weekday() in weekdays:
            dates.append(cur)
        cur = cur + timedelta(days=1)
    return dates


