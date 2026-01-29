from django.db import migrations


def upsert_periodic_task(apps, schema_editor):
    IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    schedule, _ = IntervalSchedule.objects.get_or_create(
        every=1,
        period='minutes', 
    )

    task_path = 'organisation.tasks.check_all_task_statuses'

    PeriodicTask.objects.update_or_create(
        name='Check task statuses (every 1 min)',
        defaults={
            'task': task_path,
            'interval': schedule,
            'enabled': True,
        },
    )


def remove_periodic_task(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    PeriodicTask.objects.filter(name='Check task statuses (every 1 min)').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('organisation', '0007_alter_task_status'),
        ('django_celery_beat', '0015_edit_solarschedule_events_choices'),
    ]

    operations = [
        migrations.RunPython(upsert_periodic_task, reverse_code=remove_periodic_task),
    ]
