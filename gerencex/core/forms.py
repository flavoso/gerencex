from django import forms
from gerencex.core.validators import validate_date

class RestdayForm(forms.Form):
    date = forms.DateField(label="Data", validators=[validate_date])
    note = forms.CharField(label="Descrição", max_length=50)