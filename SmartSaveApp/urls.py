"""SmartSaveApp URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from accounts.views import custom_page_not_found, custom_page_forbidden, custom_server_not_found
from django.conf import settings 
from django.conf.urls.static import static 
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    # path('', include('savings.urls')), 
    path('404/', custom_page_not_found, name='custom_404'),
    path('403/', custom_page_forbidden, name='custom_403'),
    path('500/', custom_server_not_found, name='custom_500'),
]+ static ( settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)

handler404 = 'SmartSaveApp.urls.custom_page_not_found'

handler403 = 'SmartSaveApp.urls.custom_page_forbidden'

handler500 = 'SmartSaveApp.urls.custom_server_not_found'

