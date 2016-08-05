from django import forms
from gerencex.core.models import Restday


class RestdayForm(forms.ModelForm):
    class Meta:
        model = Restday
        fields = ['date', 'note']