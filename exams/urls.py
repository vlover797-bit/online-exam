from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('create/', views.exam_create, name='exam_create'),
    path('<int:pk>/', views.exam_detail, name='exam_detail'),
    path('<int:pk>/add_question/', views.add_question, name='add_question'),
    path('<int:pk>/take/', views.take_exam, name='take_exam'),
    path('<int:pk>/submit/', views.submit_exam, name='submit_exam'),
    path('<int:pk>/result/', views.exam_result_view, name='exam_result'),
]
