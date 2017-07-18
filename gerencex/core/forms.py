from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from gerencex.core.models import Restday, Absences


class MyModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{}".format(obj.get_full_name())


class RestdayForm(forms.ModelForm):
    class Meta:
        model = Restday
        fields = ['date', 'note', 'work_hours']


class AbsencesForm(forms.Form):
    user = MyModelChoiceField(label='Colaborador',
                                  queryset=None,
                                  empty_label=None)
    begin = forms.DateField(label='Início',
                            widget=forms.TextInput(attrs={'class': 'datepicker'}))
    end = forms.DateField(label='Término',
                          widget=forms.TextInput(attrs={'class': 'datepicker'}))
    cause = forms.ChoiceField(label='Motivo', choices=Absences.ABSENCES_CHOICES)
    credit = forms.DurationField(label='Crédito',
                                 widget=forms.TextInput(attrs={'type': 'time'}),
                                 required=False,
                                 initial='0:00:00')
    debit = forms.DurationField(label='Redução de débito',
                                widget=forms.TextInput(attrs={'type': 'time'}),
                                required=False,
                                initial='0:00:00')

    def __init__(self, *args, **kwargs):
        self.users = kwargs.pop("users")
        super(AbsencesForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = self.users.order_by('first_name')

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


class GenerateBalanceForm(forms.Form):
    begin = forms.DateField(label='Data inicial',
                            required=False,
                            widget=forms.TextInput(attrs={'class':'datepicker'}))

    def clean(self):
        super(GenerateBalanceForm, self).clean()
        begin = self.cleaned_data.get("begin")

        if begin and begin > timezone.now().date():
            self.add_error('end', forms.ValidationError('Data inválida', code='inicio'))


class CheckForm(forms.Form):
    CHOICES = (('1', 'Entrada',), ('2', 'Saída',))
    user = MyModelChoiceField(label='Colaborador',
                              queryset=None,
                              empty_label=None)
    date = forms.DateField(label='Data',
                           widget=forms.TextInput(attrs={'class': 'datepicker'}))
    time = forms.TimeField(label='Horário')
    check_in = forms.ChoiceField(label='Entrada ou saída?',
                                 widget=forms.RadioSelect,
                                 choices=CHOICES)

    def __init__(self, *args, **kwargs):
        self.users = kwargs.pop("users")
        super(CheckForm, self).__init__(*args, **kwargs)
        self.fields["user"].queryset = self.users.order_by('first_name')

    def clean(self):
        super(CheckForm, self).clean()
        date = self.cleaned_data.get("date")
        today = timezone.localtime(timezone.now()).date()

        if date > today:
            self.add_error('date', forms.ValidationError(
                'Impossível registrar em data futura', code='data')
                )
