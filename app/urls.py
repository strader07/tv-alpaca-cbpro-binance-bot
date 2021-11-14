from django.contrib import admin
from django.conf import settings
from django.urls import path, include
from django.conf.urls.static import static

from main import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('i18n/', include('django.conf.urls.i18n')),
    path('accounts/', include('accounts.urls')),

    path('startbot/', views.start_bot, name='startbot'),
    path('stopbot/', views.stop_bot, name='stopbot'),

    path('execute/', views.execute, name='execute')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
