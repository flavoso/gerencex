from django import forms
from django.contrib.auth.models import User
from gerencex.core.models import Restday, Absences

class RestdayForm(forms.ModelForm):
    class Meta:
        model = Restday
        fields = ['date', 'note', 'work_hours']


class AbsencesForm(forms.Form):
    user = forms.ModelChoiceField(label='Colaborador',
                                  queryset=User.objects.all(),
                                  empty_label=None)
    begin = forms.DateField(label='Início',
                            widget=forms.TextInput(attrs={'class':'datepicker'}))
    end = forms.DateField(label='Término',
                          widget=forms.TextInput(attrs={'class':'datepicker'}))
    cause = forms.ChoiceField(label='Motivo', choices=Absences.ABSENCES_CHOICES)
    credit = forms.DurationField(label='Crédito',
                                 widget=forms.TextInput(attrs={'type':'time'}))
    debit = forms.DurationField(label='Débito',
                                widget=forms.TextInput(attrs={'type':'time'}))