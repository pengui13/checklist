from dj_rest_auth.views  import UserDetailsView
from .serializers import CustomUserDetailsSerializer, UpdateUserSerializer, CreateUserSerializer, UserListSerializer, InvitationSerializer
from rest_framework.generics import UpdateAPIView, CreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated as IsAuth
from .models import User, Invitation
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from organisation.models import Task
from organisation.tasks import send_email_task
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.db import transaction

class GetUserInfo(UserDetailsView):
    serializer_class = CustomUserDetailsSerializer
    
class UpdateUserColor(UpdateAPIView):
    serializer_class = UpdateUserSerializer
    permission_classes = [IsAuth]

    def get_object(self):
        return self.request.user

    def get_serializer(self, *args, **kwargs):
        kwargs["partial"] = True
        return super().get_serializer(*args, **kwargs)
    
class CreateUser(CreateAPIView):
    permission_classes = [IsAuth]
    serializer_class = CreateUserSerializer
    
    def create(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({'error':'Only firm admins can create users'},status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(data = request.data)
        serializer.is_valid(raise_exception = True)
        user = serializer.save(firm = request.user.firm)
        return Response(
            UserListSerializer(user).data,
            status = status.HTTP_201_CREATED
        )
        
class GetAllUsers(ListAPIView):
    permission_classes = [IsAuth]
    serializer_class = UserListSerializer
    
    def get_queryset(self):
        user = self.request.user 
        task_id = self.request.query_params.get("task_id", '')
        firm = user.firm
        
        if task_id:
            task = Task.objects.filter(id = task_id, project__firm = firm).first()
            if task:
                partner_firm = task.project.firm
                users = User.objects.filter(Q(firm = firm) | Q(firm = partner_firm))
        else:
            users = User.objects.filter(firm = firm)

        return users
    
    
class SendInvitationView(CreateAPIView):
    permission_classes = [IsAuth]
    serializer_class = InvitationSerializer
    queryset = Invitation.objects.all()
    
    def perform_create(self, serializer):
        invitation = serializer.save(
            invited_by=self.request.user,
            status='pending'
        )
        
        invite_url = f"{settings.FRONTEND_URL}/accept-invitation/{invitation.token}/"
        
        context = {
            'invitation': invitation,
            'invite_url': invite_url,
            'inviter_name': invitation.invited_by.get_full_name() or invitation.invited_by.username,
            'project_name': invitation.project.name,
            'expiry_days': 7,
            'firm_name': invitation.invited_by.firm.name if invitation.invited_by.firm else "the organization"
        }
        
        html_message = render_to_string('emails/project_invitation.html', context)
        plain_message = render_to_string('emails/project_invitation.txt', context)
        
        send_email_task.delay(
            subject=f"Invitation to collaborate on {invitation.project.name}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            html_message=html_message,
        )
        
class AcceptInvitationView(CreateAPIView):
    serializer_class = CreateUserSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        token = request.data.get("invitation_token")
        email = request.data.get("email")

        if not token or not email:
            return Response({"error": "invitation_token and email are required"}, status=400)

        try:
            invitation = Invitation.objects.select_related("project").get(token=token)
        except Invitation.DoesNotExist:
            return Response({"error": "Invalid invitation token"}, status=404)

        if invitation.status != "pending":
            return Response({"error": "This invitation is no longer valid"}, status=400)

        if invitation.is_expired:
            invitation.status = "expired"
            invitation.save(update_fields=["status"])
            return Response({"error": "This invitation is expired"}, status=400)

        if invitation.email.lower().strip() != email.lower().strip():
            return Response({"error": "Email does not match the invitation"}, status=400)

        if User.objects.filter(email=invitation.email).exists():
            return Response({"error": "User already exists. Please login."}, status=400)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(firm=None)

        invitation.status = "accepted"
        invitation.accepted_at = timezone.now()
        invitation.accepted_user = user
        invitation.save(update_fields=["status", "accepted_at", "accepted_user"])

        return Response(
            {
                "user": UserListSerializer(user).data,
                "project_id": invitation.project.id,
                "message": "Account created. Please create your firm to finish onboarding.",
            },
            status=201,
        )