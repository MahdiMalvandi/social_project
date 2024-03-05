from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

from social_project import settings


description = 'Social media website developed with Django and Rest Framework by Mahdi Malvandi. Project code source link:' \
              '<a href="https://github.com/MahdiMalvandi/social_project">soruce code</a>' \
              'Visit my GitHub to see my other portfolios.' \
              'My GitHub:<a href="https://github.com/MahdiMalvandi">my github</a>'

schema_view = get_schema_view(
    openapi.Info(
        title="Social Media Project",
        default_version='v1',
        description=description
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('posts.urls')),
    path('chat/', include('chat.urls')),
    path('notification/', include('notification.urls')),

    # Swagger
    path('docs/', schema_view.with_ui(), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
