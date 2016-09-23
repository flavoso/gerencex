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
from gerencex.core.views import home, bhauditor, bhoras, timing, restday_new, timing_new, \
    timing_fail, forgotten_checkouts, RestdayList, absences, absence_new

urlpatterns = [
    url('^logout/$', logout, {'next_page': 'home'}, name='logout'),
    url('^', include('django.contrib.auth.urls')),
    url(r'^$', home, name='home'),
    url(r'^bancodehoras/$', bhoras, name='bhoras'),
    url(r'^(?P<username>\w+)/bancodehoras', bhauditor, name='bhauditor'),
    url(r'^registro_de_ponto/novo/$', timing_new, name='timing_new'),
    url(r'^registro_de_ponto/(\d+)/$', timing, name='timing'),
    url(r'^registro_de_ponto/falha/$', timing_fail, name='timing_fail'),
    url(r'^registro_de_ponto/saidas_nao_registradas/', forgotten_checkouts,
        name='forgotten_checkouts'),
    url(r'^folgas/nova$', restday_new, name='restday_new'),
    url(r'^folgas/$', RestdayList.as_view(), 'folgas'),
    url(r'^(?P<username>\w+)/ausencias/$', absences, name='absences'),
    url(r'^ausencias/cadastrar/$', absence_new, name='absence_new'),
    url(r'^admin/', admin.site.urls),
]
