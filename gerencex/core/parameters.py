from datetime import timedelta, time

"""
'TCU' stands for Tribunal de Contas da União, the brazilian federal court for account settlement,
similar to U.S. Government Accountability Office (U.S. GAO)
"""

REGULAR_WORK_HOURS = timedelta(hours=7)                                             # TCU: 7 hours
MAX_DAILY_CREDIT = {'used': False, 'value': timedelta(hours=10)}                    # TCU: 10 hours
MAX_MONTHLY_BALANCE = {'used': False, 'value': timedelta(hours=20)}                 # TCU: 20 hours
MIN_CHECKIN_TIME = {'used': False,
                    'value': time(hour=8, minute=0, second=0)}                      # TCU: 08h00
MAX_CHECKOUT_TIME = {'used': False,
                     'value': time(hour=20, minute=0, second=0)}                    # TCU: 20h00
CHECKIN_TOLERANCE = timedelta(minutes=-10)
CHECKOUT_TOLERANCE = timedelta(minutes=5)