import datetime
import pytz


def calculate_credit(u, date):
    """
    Returns the credit for the pair user + date, as a timedelta

    Credit is calculated by summing up:
     * the credit from Timing table;
     * the credit from Absences table
    """

    from django.contrib.auth.models import User
    user = User.objects.get(pk=u.pk)

    """Get the parameters, defined for the user's office"""

    checkin_tolerance = user.userdetail.office.checkin_tolerance
    checkout_tolerance = user.userdetail.office.checkout_tolerance
    max_daily_credit = {'used': user.userdetail.office.max_daily_credit,
                        'value': user.userdetail.office.max_daily_credit_value}
    min_checkin_time = {'used': user.userdetail.office.min_checkin_time,
                        'value': user.userdetail.office.min_checkin_time_value}
    max_checkout_time = {'used': user.userdetail.office.max_checkout_time,
                         'value': user.userdetail.office.max_checkout_time_value}

    from gerencex.core.models import Timing
    tickets = [{'checkin': x.checkin, 'date_time': x.date_time}
               for x in Timing.objects.filter(user=user,
                                              date_time__date=date).all()
               ]

    """
    If the last Timing recorded is a checkin, it must not be considered in the credit calculation
    """
    if tickets[-1]['checkin']:
        del tickets[-1]

    # Calculates the credit from the Timing table
    credit = datetime.timedelta(seconds=0)

    tolerance = checkout_tolerance + checkin_tolerance

    if max_checkout_time['used'] or min_checkin_time['used']:
        tickets = adjusted_tickets(tickets, min_checkin_time, max_checkout_time)

    if len(tickets) != 0:
        for ticket in tickets:
            if not ticket['checkin']:
                chkin = tickets.index(ticket) - 1
                credit += ticket['date_time'] - tickets[chkin]['date_time'] + tolerance

    """
    Sums up the credit from Absences table
    There's only one user + date peer, due to the unique_together clause
    """

    from gerencex.core.models import Absences

    absences = [a for a in Absences.objects.filter(user=user, date=date)]
    credit_sum = datetime.timedelta(seconds=0)
    if absences:
        credit_int = absences[0].credit
        credit_sum = datetime.timedelta(seconds=credit_int)
    credit += credit_sum

    if max_daily_credit['used'] and credit > max_daily_credit['value']:
        credit = max_daily_credit['value']

    return credit


def calculate_debit(u, date):
    """
    Restday:        debit = restday.work_hours
    Absence day:    debit = REGULAR_WORK_HOURS + absence.debit
    Normal day:     debit = REGULAR_WORK_HOURS

    Debit is returned as a timedelta
    """

    from django.contrib.auth.models import User
    user = User.objects.get(pk=u.pk)

    """Get the parameters, defined for user's office"""
    regular_work_hours = user.userdetail.office.regular_work_hours

    from gerencex.core.models import Restday, Absences

    restday = Restday.objects.filter(date=date)
    absence = Absences.objects.filter(user=user, date=date)

    """If date is a restday, let's consider the work hours specified for this date"""
    if restday.count():
        return restday[0].work_hours
    elif absence.count():
        return regular_work_hours - datetime.timedelta(seconds=absence[0].debit)
    else:
        return regular_work_hours


def adjusted_tickets(tickets, min_checkin_time, max_checkout_time):
    """
    Forces the checkin time to be greater than or equal to the minimum allowed.
    Forces the checkout time to be lesser than or equal to the maximum allowed.
    """

    utc_offset = datetime.now(pytz.timezone('America/Sao_Paulo')).utcoffset()

    """Alternative way to get the correct ticket['date_time']"""
    # tz = pytz.timezone('America/Sao_Paulo')

    new_tickets = []

    for ticket in tickets:
        ticket['date_time'] = ticket['date_time'] + utc_offset

        """Alternative way"""
        # ticket['date_time'] = ticket['date_time'].astimezone(tz).replace(tzinfo=None)

        new_ticket = ticket

        if ticket['checkin'] and min_checkin_time['used']:
            if ticket['date_time'].time() < min_checkin_time['value']:
                hour = min_checkin_time['value'].hour
                minute = min_checkin_time['value'].minute
                new_ticket['date_time'] = ticket['date_time'].replace(
                    hour=hour, minute=minute)

        elif (not ticket['checkin']) and max_checkout_time['used']:
            if ticket['date_time'].time() > max_checkout_time['value']:
                hour = max_checkout_time['value'].hour
                minute = max_checkout_time['value'].minute
                new_ticket['date_time'] = ticket['date_time'].replace(
                    hour=hour, minute=minute)
        new_tickets.append(new_ticket)

    return new_tickets
