from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('platform', models.CharField(blank=True, max_length=50, null=True)),
                ('intent', models.CharField(max_length=80)),
                ('user_message', models.TextField()),
                ('assistant_reply', models.TextField()),
                ('analytics_summary', models.JSONField(blank=True, null=True, default=dict)),
                ('metadata', models.JSONField(blank=True, null=True, default=dict)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ChatHistory_created', to=django.conf.settings.AUTH_USER_MODEL)),
                ('deleted_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ChatHistory_deleted', to=django.conf.settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ChatHistory_updated', to=django.conf.settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chat_histories', to=django.conf.settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ai_chat_history',
            },
        ),
        migrations.AddIndex(
            model_name='chathistory',
            index=models.Index(fields=['user'], name='ai_chathis_user_id_7deeaa_idx'),
        ),
        migrations.AddIndex(
            model_name='chathistory',
            index=models.Index(fields=['platform'], name='ai_chathis_platform_3d4e3d_idx'),
        ),
        migrations.AddIndex(
            model_name='chathistory',
            index=models.Index(fields=['created_at'], name='ai_chathis_created_at_03c8be_idx'),
        ),
    ]
