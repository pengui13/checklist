from rest_framework import serializers
from .models import Firm, Project, Task, TaskAttachment
from users.models import User
# class OnboardingSerializer(serializers.Serializer):
#     color = serializers.CharField(max_length = 6)
    
    
class FirmSerializer(serializers.ModelSerializer):
    creator = serializers.SerializerMethodField()
    admins = serializers.SerializerMethodField()
    
    def get_creator(self, obj):
        creator = User.objects.filter(firm=obj, is_creator=True).first()
        return creator.username if creator else None
    
    def get_admins(self, obj):
        admins = User.objects.filter(firm=obj, is_admin=True).values(
            'id', 'username', 'first_name', 'last_name', 'email'
        )
        return list(admins)
    
    class Meta:
        model = Firm
        fields = ['name', 'id', 'creator', 'admins']
        
class ProjectSerializer(serializers.ModelSerializer):
    firm = FirmSerializer(read_only = True)
    partner = FirmSerializer(read_only = True, required=False)
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['firm', 'partner']


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAttachment
        fields = '__all__'
        
class TaskSerializer(serializers.ModelSerializer):
    attachments = AttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ("task", "uploaded_by", "filename", "file_size", "uploaded_at")

        