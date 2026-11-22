from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .forms import LoginForm

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('produk/tambah/', views.ProductCreateView.as_view(), name='product_create'),
    path('produk/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('produk/<int:pk>/hapus/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('produk/ekspor/', views.export_csv, name='product_export'),
]