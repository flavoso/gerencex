from django.core.exceptions import ValidationError


def validate_date(date):
    weekend = [5, 6]
    if date.weekday() in weekend:
        raise ValidationError('Data inválida: fim de semana.',
                              'weekend')
