from django.conf.urls import include, url
from django.contrib import admin
admin.autodiscover()

from rest_framework.urlpatterns import format_suffix_patterns

import os

from recomendacao import views

from recomendacao.const import APP_NAME, CSE_ID


api_urlpatterns = [
    url(r'^v2/post/$', views.EnviaTextoV2.as_view(), name='post-v2'),
    url(r'^v3/post/$', views.EnviaTextoV3.as_view(), name='post-v3'),
]
api_urlpatterns = format_suffix_patterns(api_urlpatterns)

urlpatterns = [
    # Examples:
    # url(r'^$', 'recomendacao.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    
    #project
    url(r'^$', views.TemplateViewContext.as_view(template_name=os.path.join(APP_NAME, 'inicio.html')), name='inicio'),
    url(r'^v1/$', views.ViewBusca.as_view(template_name=os.path.join(APP_NAME, 'busca.html')), name='v1'),
    url(r'^v2/$', views.ViewBusca.as_view(template_name=os.path.join(APP_NAME, 'busca-post-v2.html')), name='v2'),
    url(r'^v3/$', views.ViewBusca.as_view(template_name=os.path.join(APP_NAME, 'busca-post-v3.html')), name='v3'),
    
    url(r'^envia-texto-sobek/$', views.envia_texto_sobek, name='envia_texto_sobek'),
    
    url(r'^jquery.redirect.csrf.js$', views.TemplateViewContext.as_view(template_name=os.path.join(APP_NAME, 'js', 'jquery.redirect.csrf.js')), name='jquery.redirect.csrf'),
    url(r'^js-aux/$', views.TemplateViewContext.as_view(template_name=os.path.join(APP_NAME, 'js', 'js-aux.js')), name='js-aux'),
    url(r'^js-v1/$', views.TemplateViewContext.as_view(template_name=os.path.join(APP_NAME, 'js', 'js-v1.js'), extra_context={'CSE_ID': CSE_ID}), name='js-v1'),
    url(r'^js-v2/$', views.TemplateViewContext.as_view(template_name=os.path.join(APP_NAME, 'js', 'js-v2.js')), name='js-v2'),
    url(r'^js-v3/$', views.TemplateViewContext.as_view(template_name=os.path.join(APP_NAME, 'js', 'js-v3.js')), name='js-v3'),
    
    #admin
    url(r'^admin/', include(admin.site.urls)),
]
urlpatterns += api_urlpatterns
