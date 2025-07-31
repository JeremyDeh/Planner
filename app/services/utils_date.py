from dateutil.rrule import rrule, DAILY, WEEKLY, MONTHLY


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
