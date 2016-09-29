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
                                 widget=forms.TextInput(attrs={'type':'time'}),
                                 required=False,
                                 initial='0:00:00')
    debit = forms.DurationField(label='Débito',
                                widget=forms.TextInput(attrs={'type':'time'}),
                                required=False,
                                initial='0:00:00')

    def clean(self):
        super(AbsencesForm, self).clean()
        begin = self.cleaned_data.get("begin")
        end = self.cleaned_data.get("end")

        if begin and end:
            if end < begin:
                # raise forms.ValidationError('Data inválida', code='termino')
                self.add_error('end', forms.ValidationError(
                    'Data de término menor que a de início', code='termino')
                    )
