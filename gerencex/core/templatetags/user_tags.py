from django import template


register = template.Library()


@register.filter('has_group')
def has_group(user, group_name):
    """
    Checks if 'user' belongs to 'group_name' group
    """
    groups = user.groups.all().values_list('name', flat=True)
    return True if group_name in groups else False
