from rest_framework.views import APIView
from misc.permissions import IsAuth
from rest_framework.generics import ListCreateAPIView
from .models import Firm, Project, Task, TaskAttachment
from rest_framework.exceptions import NotFound
from .serializers import FirmSerializer, ProjectSerializer, TaskSerializer, AttachmentSerializer
from rest_framework.response import Response
from django.db import transaction
from rest_framework import status 
from organisation.tasks import send_email_task
from users.models import Invitation
from django.db.models import Q

class GetFirms(ListCreateAPIView):
    permission_classes = [IsAuth]
    queryset = Firm.objects.all()
    serializer_class = FirmSerializer

    @transaction.atomic
    def perform_create(self, serializer):
        firm = serializer.save()

        user = self.request.user
        user.firm = firm
        user.is_creator = True
        user.is_admin = True
        user.save(update_fields=["firm", "is_creator", "is_admin"])

        invitations = (
            Invitation.objects
            .select_related("project")
            .filter(
                accepted_user=user,
                status="accepted",
            )
        )

        project_ids = invitations.values_list("project_id", flat=True).distinct()
        Project.objects.filter(id__in=project_ids).exclude(partner=firm).update(partner=firm)

class JoinFirm(APIView):
    permission_classes = [IsAuth]
    def post(self, request):
        user = request.user
        firm_id = request.data.get('firm_id', '')
        user.firm = Firm.objects.get(id = firm_id)
        user.save()
        return Response({'success': True})
    
class CheckOnboarding(APIView):
    permission_classes = [IsAuth]
    def get(self, request):
        user = request.user
        return Response({
            'needs_onboarding':user.needs_onboarding(),
               'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'has_firm': user.firm is not None,
                'has_color': bool(user.hex_color),
                'firm': FirmSerializer(user.firm).data if user.firm else None,
                'hex_color': user.hex_color
            }
        })
        
class ProjectView(ListCreateAPIView):
    permission_classes = [IsAuth]
    serializer_class = ProjectSerializer
    
    def get_queryset(self):
        firm = self.request.user.firm
        return Project.objects.filter(Q(firm = firm) | Q(partner = firm))
    
    def perform_create(self, request):
        partner_id = self.request.data.get('partner')
        partner = None
        if partner_id:
            partner = Firm.objects.filter(id = partner_id).first() 
        serializer = self.get_serializer(data = self.request.data)
        serializer.is_valid(raise_exception = True)
        project = serializer.save(firm = self.request.user.firm, partner = partner)
        return Response(
            ProjectSerializer(project).data,
            status = status.HTTP_201_CREATED
        )
    
class TaskView(ListCreateAPIView):
    permission_classes = [IsAuth]
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        queryset = Task.objects.filter(project__id=project_id)
        return queryset
    def perform_create(self, serializer):
        task = serializer.save()
        emails = list(task.assigned_users.values_list('email', flat = True))
        if not emails:
            return 
        transaction.on_commit(lambda: send_email_task.delay(
                    "New Task",
                    "You received new task",
                    emails)
            )       
        
class TaskAttachmentView(ListCreateAPIView):
    permission_classes = [IsAuth]
    serializer_class = AttachmentSerializer

    def get_queryset(self):
        task_id = self.kwargs["task_id"]
        return TaskAttachment.objects.filter(task_id=task_id)

    def perform_create(self, serializer):
        task_id = self.kwargs["task_id"]
        try:
            task = Task.objects.get(id=task_id)

                
        except Task.DoesNotExist:
            raise NotFound("Task not found")

        serializer.save(
            task=task,
            uploaded_by=self.request.user,
        )
        
 
             