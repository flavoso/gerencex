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
    timing_fail, forgotten_checkouts, absences, absence_new, rules

urlpatterns = [
    url('^logout/$', logout, {'next_page': 'home'}, name='logout'),
    url('^', include('django.contrib.auth.urls')),
    url(r'^$', home, name='home'),
    url(r'^bancodehoras/$', hours_bank, name='hours_bank'),
    url(r'^bancodehoras/(?P<username>\w+)/$', my_hours_bank, name='my_hours_bank'),
    url(r'^bancodehoras/regras/$', rules, name='rules'),
    url(r'^registro_de_ponto/novo/$', timing_new, name='timing_new'),
    url(r'^registro_de_ponto/(\d+)/$', timing, name='timing'),
    url(r'^registro_de_ponto/falha/$', timing_fail, name='timing_fail'),
    url(r'^registro_de_ponto/saidas_nao_registradas/', forgotten_checkouts,
        name='forgotten_checkouts'),
    url(r'^afastamentos/cadastrar/$', absence_new, name='absence_new'),
    url(r'^afastamentos/(?P<username>\w+)/$', absences, name='absences'),
    url(r'^admin/', admin.site.urls),
]
