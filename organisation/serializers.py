from rest_framework import serializers
from .models import Firm, Project, Task, TaskAttachment
# class OnboardingSerializer(serializers.Serializer):
#     color = serializers.CharField(max_length = 6)
    
    
class FirmSerializer(serializers.ModelSerializer):
    # workers = serializers.SerializerMethodField()
    
    # def get_workers(self, obj):
    #     return obj.firms.count()
    
    class Meta:
        model = Firm
        fields = ['name', 'id']
        
class ProjectSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['firm']


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

        