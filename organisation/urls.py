from django.urls import path, include
from . import views
urlpatterns = [
    path('firms/', views.GetFirms.as_view(), name = 'firms'),
    path('join_firm/', views.JoinFirm.as_view(), name = 'join-firm'),
    path('check_onboarding/', views.CheckOnboarding.as_view(), name = 'check_onboarding'),
    path('projects/', views.ProjectView.as_view(), name = 'projects '),
    path("tasks/", views.TaskView.as_view(), name="task-list-create"),
    path("tasks/<int:task_id>/attachments/", views.TaskAttachmentView.as_view(), name="task-attachment-list-create")
]