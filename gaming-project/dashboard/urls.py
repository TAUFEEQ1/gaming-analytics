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
]
