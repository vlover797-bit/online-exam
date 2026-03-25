"""
URL configuration for secure_exam project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from django.http import HttpResponse
from django.db import connections
import traceback

def test_db(request):
    try:
        conn = connections['default']
        conn.ensure_connection()
        # For MongoDB, doing a quick query guarantees it talked to the server
        from accounts.models import User
        count = User.objects.count()
        return HttpResponse(f"<h1>MongoDB Connection Successful!</h1><p>Found {count} users.</p>")
    except Exception as e:
        return HttpResponse(f"<h1>MongoDB Connection FAILED</h1><pre>{traceback.format_exc()}</pre>")

urlpatterns = [
    path('test-db/', test_db),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('exams/', include('exams.urls')),
    path('proctoring/', include('proctoring.urls')),
    path('', include('accounts.urls')), # Redirect root to accounts for now
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
