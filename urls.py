from django.conf.urls import url
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('like_announce/', views.like_announce, name='like_announce'),
    path('get_subcategories/', views.get_subcategories, name='get_subcategories'),
    path('create_product/', views.create_product, name='create_product'),
    path('edit_product/<int:pk>', views.edit_product, name='edit_product'),
    path('delete_product/<int:pk>', views.delete_product, name='delete_product'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
