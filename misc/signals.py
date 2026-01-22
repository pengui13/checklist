from django.db.models.signals import post_save, pre_save,post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from threading import local

from .models import ActivityLog
from organisation.models import Project, Task

_thread_locals = local()

def set_current_user(user, ip_address=None):
    _thread_locals.user = user
    _thread_locals.ip_address = ip_address
    
def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_ip():
    return getattr(_thread_locals, 'ip_address', None)

def clear_current_user():
    _thread_locals.user = None
    _thread_locals.ip_address = None

TRACKED_MODELS = [Project, Task]

IGNORED_FIELDS = ['id', 'created_at']


def get_instance_key(instance):
    return f"P{instance.__class__.__name__}_{instance.pk}"

def store_original_state(instance):
    if not hasattr(_thread_locals, 'original_states'):
        _thread_locals.original_states = {}
    
    if instance.pk:
        original = {}
        for field in instance._meta.fields:
            if field.name not in IGNORED_FIELDS:
                value = getattr(instance, field.name)
                if field.is_relation and value is not None:
                    value = value.pk if hasattr(value, 'pk') else str(value)
                original[field.name] = value
        
        _thread_locals.original_states[get_instance_key(instance)] = original




def get_original_state(instance):
    if not hasattr(_thread_locals, 'original_states'):
        return None
    return _thread_locals.original_states.get(get_instance_key(instance))


def get_changes(instance, original):
    if not original:
        return {}
    
    changes = {}
    for field in instance._meta.fields:
        if field.name in IGNORED_FIELDS:
            continue
        
        new_value = getattr(instance, field.name)
        
        if field.is_relation and new_value is not None:
            new_value = new_value.pk if hasattr(new_value, 'pk') else str(new_value)
        
        old_value = original.get(field.name)
        
        if old_value != new_value:
            changes[field.name] = {
                'old': old_value,
                'new': new_value
            }
    
    return changes


def get_firm_from_instance(instance):
    if hasattr(instance, 'firm'):
        return instance.firm
    if hasattr(instance, 'project') and hasattr(instance.project, 'firm'):
        return instance.project.firm
    return None


def get_instance_description(instance, action):
    model_name = instance.__class__.__name__
    
    if hasattr(instance, 'name'):
        identifier = instance.name
    elif hasattr(instance, 'title'):
        identifier = instance.title
    else:
        identifier = str(instance.pk)
    
    return f"{model_name} '{identifier}' {action}"

def clear_original_state(instance):
    if hasattr(_thread_locals, 'original_states'):
        key = get_instance_key(instance)
        if key in _thread_locals.original_states:
            del _thread_locals.original_states[key]

@receiver(pre_save)
def track_pre_save(sender, instance, **kwargs):
    if sender in TRACKED_MODELS:
        store_original_state(instance)


@receiver(post_save)
def track_post_save(sender, instance, created, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    
    if sender == ActivityLog:  
        return
    
    user = get_current_user()
    ip_address = get_current_ip()
    firm = get_firm_from_instance(instance)
    
    if created:
        ActivityLog.log(
            action=ActivityLog.Action.CREATE,
            user=user,
            firm=firm,
            obj=instance,
            description=get_instance_description(instance, 'created'),
            ip_address=ip_address,
        )
    else:
        original = get_original_state(instance)
        changes = get_changes(instance, original)
        
        if changes:  
            ActivityLog.log(
                action=ActivityLog.Action.UPDATE,
                user=user,
                firm=firm,
                obj=instance,
                description=get_instance_description(instance, 'updated'),
                changes=changes,
                ip_address=ip_address,
            )
    
    clear_original_state(instance)


@receiver(post_delete)
def track_post_delete(sender, instance, **kwargs):
    if sender not in TRACKED_MODELS:
        return
    
    user = get_current_user()
    ip_address = get_current_ip()
    firm = get_firm_from_instance(instance)
    
    ActivityLog.log(
        action=ActivityLog.Action.DELETE,
        user=user,
        firm=firm,
        obj=None, 
        description=get_instance_description(instance, 'deleted'),
        changes={'deleted_object': {
            'model': sender.__name__,
            'pk': instance.pk,
            'str': str(instance),
        }},
        ip_address=ip_address,
    )