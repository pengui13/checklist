from rest_framework import serializers
from django.contrib.auth import get_user_model
from organisation.models import Firm
from .models import Invitation
User = get_user_model()

class FirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = ['id', 'name']

class BaseUserSerializer(serializers.ModelSerializer):
    
    def validate_username(self, value):
        if User.objects.filter(username = value).exists():
            raise serializers.ValidationError('Username already exists')
        return value

    def validate_email(self, value):
        if User.objects.filter(email = value).exists():
            raise serializers.ValidationError('Email already exists')
        return value
    
    def validate_hex_color(self, value):
        
        if len(value) != 6:
            raise serializers.ValidationError('Hex color must be exactly 6 characters')
        try:
            int(value, 16)
        except ValueError:
            raise serializers.ValidationError('Invalid hex color. Use only 0-9 and A-F')
        return value
    
    class Meta:
        model = User
        abstract = True

class CustomUserDetailsSerializer(BaseUserSerializer):
    
    firm = FirmSerializer(read_only = True)
    needs_onboarding = serializers.SerializerMethodField()
    
    def get_needs_onboarding(self, obj):
        return obj.needs_onboarding()
    
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'hex_color',
            'firm',
            'needs_onboarding',
            'is_admin'
        ]
        read_only_fields = ['id', 'username', 'email', 'is_admin']
        
        

class UpdateUserSerializer(BaseUserSerializer):
    

    class Meta:
        model = User
        fields = ('hex_color', 'first_name', 'last_name')
        extra_kwargs = {
            "hex_color": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }
    
    
class UserListSerializer(BaseUserSerializer):
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ['id', 'username', 'email', 'is_creator']
        
class CreateUserSerializer(BaseUserSerializer):
    password = serializers.CharField(write_only = True, min_length = 8,style={'input_type': 'password'})
    hex_color = serializers.CharField(min_length = 6, max_length = 6, required = True)
    is_admin = serializers.BooleanField(default = False)
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(
            password = password,
            **validated_data
        )
        return user
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'first_name',
            'last_name',
            'hex_color',
            'is_admin'
        ]
        extra_kwargs = {
            'username': {'required': True},
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
        
class InvitationSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source = 'project.name', read_only = True)
    invited_by_name = serializers.CharField(source = 'invited_by.get_full_name', read_only = True)
    
    class Meta:
        model = Invitation
        fields = ['id', 'email', 'project', 'project_name', 'invited_by', 
                 'invited_by_name', 'status', 'created_at', 'expires_at']
        read_only_fields = ['id', 'invited_by', 'status', 'created_at', 'expires_at']
    
    def validate_email(self, value):
        if User.objects.filter(email = value).exists():
            raise serializers.ValidationError("A user with this email already exists")
        return value
    
    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            project = data.get('project')
            if project and project.firm != user.firm:
                raise serializers.ValidationError("You can only invite partners to your firm's projects")
        return data