import datetime
from django.utils import timezone
from gerencex.core.models import Restday, Timing, Absences

current_tz = timezone.get_current_timezone()


class UserParameters:

    def __init__(self, user):
        """
        Parameters get only from user settings
        """
        self.user = user
        self.office = user.userdetail.office
        self.start_control_date = self.office.hours_control_start_date
        self.opening_balance = user.userdetail.opening_hours_balance
        self.regular_work_hours = self.office.regular_work_hours
        self.start_control_date = self.office.hours_control_start_date
        self.checkin_tolerance = self.office.checkin_tolerance
        self.checkout_tolerance = self.office.checkout_tolerance
        self.max_daily_credit = {'used': self.office.max_daily_credit,
                                 'value': self.office.max_daily_credit_value}
        self.min_checkin_time = {'used': self.office.min_checkin_time,
                                 'value': self.office.min_checkin_time_value}
        self.max_checkout_time = {'used': self.office.max_checkout_time,
                                  'value': self.office.max_checkout_time_value}
        self.min_work_hours_for_credit = {'used': self.office.min_work_hours_for_credit,
                                          'value': self.office.min_work_hours_for_credit_value}
        self.tolerance = self.checkin_tolerance + self.checkout_tolerance


class DateParameters:

    def __init__(self, date):
        """
        Parameters get only from date
        """
        self.date = date
        self.zero = datetime.timedelta(seconds=0)
        self.is_restday = bool(Restday.objects.filter(date=self.date))
        self.is_weekend = self.date.weekday() in (5, 6)


class Tickets(UserParameters, DateParameters):
    def __init__(self, user, date):
        UserParameters.__init__(self, user)
        DateParameters.__init__(self, date)

    def tickets(self):
        """
        :return: The list of check in and checkout tickets for a given user, in a given date
        """
        day_before = self.date - datetime.timedelta(days=1)
        day_after = self.date + datetime.timedelta(days=1)
        tickets1 = [t for t in Timing.objects.filter(
                    user=self.user,
                    date_time__date__gte=day_before,
                    date_time__date__lte=day_after).all()
                    ]

        tickets2 = [x for x in tickets1
                    if x.date_time.astimezone(current_tz).date() == self.date
                    ]
        return [{'checkin': y.checkin,
                 'date_time': y.date_time.astimezone(current_tz)}
                 for y in tickets2
                ]

    def adjusted_tickets(self):
        """
        Forces the check in time to be greater than or equal to the minimum allowed.
        Forces the checkout time to be lesser than or equal to the maximum allowed.
        """

        # utc_offset = datetime.now(pytz.timezone('America/Sao_Paulo')).utcoffset()
        #
        # """Alternative way to get the correct ticket['date_time']"""
        # tz = pytz.timezone('America/Sao_Paulo')

        new_tickets = []

        for ticket in self.tickets():
            # ticket['date_time'] = ticket['date_time'] + utc_offset
            #
            # """Alternative way"""
            # ticket['date_time'] = ticket['date_time'].astimezone(tz).replace(tzinfo=None)

            new_ticket = ticket

            if ticket['checkin'] and self.min_checkin_time['used']:
                if ticket['date_time'].time() < self.min_checkin_time['value']:
                    hour = self.min_checkin_time['value'].hour
                    minute = self.min_checkin_time['value'].minute
                    new_ticket['date_time'] = ticket['date_time'].replace(
                        hour=hour, minute=minute)

            elif (not ticket['checkin']) and self.max_checkout_time['used']:
                if ticket['date_time'].time() > self.max_checkout_time['value']:
                    hour = self.max_checkout_time['value'].hour
                    minute = self.max_checkout_time['value'].minute
                    new_ticket['date_time'] = ticket['date_time'].replace(
                        hour=hour, minute=minute)
            new_tickets.append(new_ticket)

        return new_tickets


class DateData(Tickets):
    """
    The instance returns the credit and debit given a combination of user and date.
    """
    def __init__(self, user, date):
        """
        Data get from the combination of user and date
        """
        Tickets.__init__(self, user, date)
        self.is_opening_balance = self.date == self.start_control_date
        self.is_absence = bool(Absences.objects.filter(date=self.date, user=self.user))
        self.is_regular = not (
            self.is_restday or
            self.is_weekend or
            self.is_absence or
            self.is_opening_balance
        )


    #####################
    #   Debit methods   #
    #####################

    def regular_debit(self):
        if self.is_weekend:
            return self.zero
        if self.is_restday:
            restday = Restday.objects.get(date=self.date)
            return restday.work_hours
        return self.regular_work_hours

    def opening_debit_delta(self):
        if self.is_opening_balance and self.opening_balance < 0:
            return datetime.timedelta(seconds=-self.opening_balance)
        return self.zero

    def absence_debit_delta(self):
        if self.is_absence and not self.is_weekend and not self.is_restday:
            absence = Absences.objects.get(user=self.user, date=self.date)
            debit_int = -absence.debit
            return datetime.timedelta(seconds=debit_int)
        return self.zero

    def debit(self):
        debit = self.regular_debit() + \
                self.opening_debit_delta() + \
                self.absence_debit_delta()
        return debit

    #####################
    #   Credit methods  #
    #####################

    def regular_credit(self):
        credit = self.zero
        tickets = self.tickets()

        if self.max_checkout_time['used'] or self.min_checkin_time['used']:
            tickets = self.adjusted_tickets()

        # If the first Timing recorded is a checkout, it must not be considered in the
        # credit calculation
        if len(tickets) != 0 and not tickets[0]['checkin']:
            del tickets[0]

        # If the last Timing recorded is a checkin, it must not be considered in the
        # credit calculation
        if len(tickets) != 0 and tickets[-1]['checkin']:
            del tickets[-1]

        # Calculate the credit out of tickets
        if len(tickets) != 0:
            for ticket in tickets:
                if not ticket['checkin']:
                    chkin = tickets.index(ticket) - 1
                    credit += ticket['date_time'] - tickets[chkin]['date_time']

        credit += self.tolerance if credit else self.zero

        return credit

    def opening_credit_delta(self):
        """
        :return: The initial credit set up for a user
        """
        if self.is_opening_balance and self.opening_balance >= 0:
            return datetime.timedelta(seconds=self.opening_balance)
        return self.zero

    def absence_credit_delta(self):
        """
        :return: The credit due to courses, external work etc.
        """
        if self.is_absence:
            absence = Absences.objects.get(user=self.user, date=self.date)
            credit_int = absence.credit
            return datetime.timedelta(seconds=credit_int)
        return self.zero

    def min_work_hours_for_credit_delta(self):
        """
        :return: A negative timedelta if needed, due to min_work_hours_for_credit restriction
        """
        min_work_hours_for_credit = self.min_work_hours_for_credit
        regular_work_hours = self.regular_work_hours
        tentative_credit = self.regular_credit() + self.absence_credit_delta()
        delta = self.zero

        if min_work_hours_for_credit['used'] and not (self.is_restday or self.is_weekend):
            if regular_work_hours < tentative_credit <= min_work_hours_for_credit['value']:
                delta = -(tentative_credit - regular_work_hours)
            if tentative_credit > min_work_hours_for_credit['value']:
                delta = -(min_work_hours_for_credit['value'] - regular_work_hours)
        return delta

    def max_daily_credit_delta(self):
        """
        :return: A negative timedelta if needed, due to max_daily_credit restriction
        """
        max_daily_credit = self.max_daily_credit
        credit = self.regular_credit() + \
                 self.absence_credit_delta() + \
                 self.min_work_hours_for_credit_delta()
        if max_daily_credit['used'] and credit > max_daily_credit['value']:
            return -(credit - max_daily_credit['value'])
        return self.zero

    def credit(self):
        credit = self.regular_credit() + \
                 self.opening_credit_delta() + \
                 self.absence_credit_delta() + \
                 self.min_work_hours_for_credit_delta() + \
                 self.max_daily_credit_delta()
        return credit
