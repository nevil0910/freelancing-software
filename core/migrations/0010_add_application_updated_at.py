# The core_application table was already created by a previously applied migration
# that lacked the updated_at column. This migration uses SeparateDatabaseAndState:
# - State: records the full CreateModel (so Django tracks the complete model)
# - DB: runs raw SQL to add only the missing updated_at column

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_job_tagline'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # State operations: Django tracks the full Application model
            state_operations=[
                migrations.CreateModel(
                    name='Application',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('message', models.TextField(help_text='Cover letter or clarification message')),
                        ('status', models.CharField(choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('freelancer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to=settings.AUTH_USER_MODEL)),
                        ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='core.job')),
                    ],
                    options={
                        'ordering': ['-created_at'],
                        'unique_together': {('job', 'freelancer')},
                    },
                ),
            ],
            # Database operations: table already exists; only add the missing column via raw SQL
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE core_application ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW();',
                    reverse_sql='ALTER TABLE core_application DROP COLUMN IF EXISTS updated_at;',
                ),
            ],
        ),
    ]
