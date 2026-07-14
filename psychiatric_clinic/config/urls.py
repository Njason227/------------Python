from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.reports.views import home_redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_redirect, name='home'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('references/', include('apps.references.urls', namespace='references')),
    path('patients/', include('apps.patients.urls', namespace='patients')),
    path('distribution/', include('apps.distribution.urls', namespace='distribution')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
