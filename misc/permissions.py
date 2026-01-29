from rest_framework.permissions import BasePermission
from .signals import set_current_user
from organisation.models import Firm

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class IsAuth(BasePermission):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            set_current_user(request.user, get_client_ip(request))
            return True
        return False
    

class IsFirmaAdmin(BasePermission):
    def has_permission(self, request, view):
        firm_id = request.query_params.get('firm')
        firm = Firm.objects.filter(id = firm_id).first()
        if request.user.is_admin and request.user.firm == firm:
            return True
        return False