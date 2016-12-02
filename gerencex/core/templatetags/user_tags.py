import datetime

from django import template


register = template.Library()


@register.filter('has_group')
def has_group(user, group_name):
    """
    Checks if 'user' belongs to 'group_name' group
    """
    groups = user.groups.all().values_list('name', flat=True)
    return True if group_name in groups else False


@register.filter('timedelta')
def timedelta(delta):
    """
    :param delta: a datetime.timedelta value
    :return: a string in the format H:i:s or -H:i:s
    """
    seconds = int(delta.total_seconds())

    if seconds < 0:
        return '-{}'.format(datetime.timedelta(seconds=abs(seconds)))
    return str(datetime.timedelta(seconds=seconds))
