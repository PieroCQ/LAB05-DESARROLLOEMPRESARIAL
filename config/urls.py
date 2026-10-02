"""URL configuration: admin site, movies catalogue and news portal."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('news/', include('news.urls')),
    path('', include('movies.urls')),
]

# Serve media files only during development. In production the web
# server (nginx, Apache...) must serve them instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
