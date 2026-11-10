from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', include('core.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Para demos sin almacenamiento externo: SERVE_MEDIA=True sirve /media/ desde Django.
if not settings.DEBUG and settings.SERVE_MEDIA:
    from django.urls import re_path
    from django.views.static import serve
    urlpatterns += [re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT})]
