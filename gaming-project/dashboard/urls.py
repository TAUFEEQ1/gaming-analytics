from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('operators/', views.operators_list, name='operators_list'),
    path('excluded-operators/', views.excluded_operators_list, name='excluded_operators_list'),
    path('excluded-operator/<str:operator_code>/', views.excluded_operator_detail, name='excluded_operator_detail'),
    path('anomalies/', views.anomalies_list, name='anomalies_list'),
    path('profile/', views.profile, name='profile'),
    path('operator/<str:operator_code>/', views.performance_detail, name='performance_detail'),
    
    # Tax Variance Analysis URLs
    path('tax-variance/', views.tax_variance_dashboard, name='tax_variance_dashboard'),
    path('tax-variance/upload/', views.tax_variance_upload, name='tax_variance_upload'),
    path('tax-variance/calculate/', views.calculate_tax_variance, name='calculate_tax_variance'),
    path('tax-variance/operator/<str:operator_name>/', views.operator_tax_detail, name='operator_tax_detail'),
]
