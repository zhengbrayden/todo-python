from django.contrib import admin
from django.urls import path, include
from todos.views import HomeView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('todos.urls')),
]
