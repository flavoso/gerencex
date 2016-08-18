from django import forms
from gerencex.core.models import Restday, Timing


class RestdayForm(forms.ModelForm):
    class Meta:
        model = Restday
        fields = ['date', 'note', 'work_hours']