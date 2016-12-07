"""gerencex URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.views import logout
from gerencex.core.views import home, my_hours_bank, hours_bank, timing, timing_new, \
    timing_fail, forgotten_checkouts, absences, absence_new, rules, calculate_hours_bank, my_tickets, \
    restdays, calculations, absences_office, office_tickets

urlpatterns = [
    url('^logout/$', logout, {'next_page': 'home'}, name='logout'),
    url('^', include('django.contrib.auth.urls')),
    url(r'^$', home, name='home'),
    url(r'^banco_de_horas/$', hours_bank, name='hours_bank'),
    url(r'^banco_de_horas/(?P<username>\w+)/(?P<year>\d{4})/(?P<month>\d{1,2})/$', my_hours_bank,
        name='my_hours_bank'),
    url(r'^banco_de_horas/calcular', calculate_hours_bank, name='calculate_hours_bank'),
    url(r'^banco_de_horas/regras/$', rules, name='rules'),
    url(r'^banco_de_horas/(?P<username>\w+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$',
        calculations, name='calculations'),
    url(r'^registros_de_ponto/novo/$', timing_new, name='timing_new'),
    url(r'^registros_de_ponto/(\d+)/$', timing, name='timing'),
    url(r'^registros_de_ponto/$', office_tickets, name='office_tickets'),
    url(r'^registros_de_ponto/falha/$', timing_fail, name='timing_fail'),
    url(r'^registros_de_ponto/saidas_nao_registradas/', forgotten_checkouts,
        name='forgotten_checkouts'),
    url(r'^afastamentos/cadastrar/$', absence_new, name='absence_new'),
    url(r'^afastamentos/(?P<username>\w+)/(?P<year>\d{4})/$', absences, name='absences'),
    url(r'^afastamentos/$', absences_office, name='absences_office'),
    url(r'^registros_de_ponto/(?P<username>\w+)/(?P<year>\d{4})/(?P<month>\d{1,2})/$', my_tickets,
        name='my_tickets'),
    url(r'^dias_inuteis/(?P<year>\d{4})/$', restdays, name='restdays'),
    url(r'^admin/', admin.site.urls),
]

