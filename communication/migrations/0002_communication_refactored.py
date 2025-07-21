# Generated migration for communication refactoring

from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommunicationMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200, verbose_name='Título')),
                ('content', models.TextField(verbose_name='Conteúdo')),
                ('summary', models.CharField(blank=True, max_length=500, verbose_name='Resumo')),
                ('message_type', models.CharField(choices=[('announcement', 'Comunicado'), ('memo', 'Memorando'), ('newsletter', 'Newsletter'), ('notification', 'Notificação'), ('alert', 'Alerta')], default='announcement', max_length=50, verbose_name='Tipo de Mensagem')),
                ('priority', models.CharField(choices=[('low', 'Baixa'), ('medium', 'Média'), ('high', 'Alta'), ('urgent', 'Urgente')], default='medium', max_length=20, verbose_name='Prioridade')),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('scheduled', 'Agendado'), ('published', 'Publicado'), ('archived', 'Arquivado')], default='draft', max_length=20, verbose_name='Status')),
                ('category', models.CharField(choices=[('general', 'Geral'), ('policy', 'Política'), ('event', 'Evento'), ('training', 'Treinamento'), ('safety', 'Segurança'), ('hr', 'Recursos Humanos'), ('technical', 'Técnico'), ('financial', 'Financeiro'), ('social', 'Social')], default='general', max_length=50, verbose_name='Categoria')),
                ('tags', models.CharField(blank=True, max_length=200, verbose_name='Tags')),
                ('requires_response', models.BooleanField(default=False, verbose_name='Requer Resposta')),
                ('allow_responses', models.BooleanField(default=True, verbose_name='Permite Respostas')),
                ('response_deadline', models.DateTimeField(blank=True, null=True, verbose_name='Prazo para Resposta')),
                ('is_pinned', models.BooleanField(default=False, verbose_name='Fixado')),
                ('publish_date', models.DateTimeField(blank=True, null=True, verbose_name='Data de Publicação')),
                ('expire_date', models.DateTimeField(blank=True, null=True, verbose_name='Data de Expiração')),
                ('view_count', models.IntegerField(default=0, verbose_name='Visualizações')),
                ('response_count', models.IntegerField(default=0, verbose_name='Respostas')),
                ('engagement_score', models.FloatField(default=0.0, verbose_name='Score de Engajamento')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='Metadados')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='authored_messages', to=settings.AUTH_USER_MODEL, verbose_name='Autor')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Mensagem de Comunicação',
                'verbose_name_plural': 'Mensagens de Comunicação',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MessageRecipient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_read', models.BooleanField(default=False, verbose_name='Lida')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Lida em')),
                ('is_archived', models.BooleanField(default=False, verbose_name='Arquivada')),
                ('archived_at', models.DateTimeField(blank=True, null=True, verbose_name='Arquivada em')),
                ('delivery_status', models.CharField(choices=[('pending', 'Pendente'), ('delivered', 'Entregue'), ('failed', 'Falhou'), ('bounced', 'Rejeitada')], default='pending', max_length=20, verbose_name='Status de Entrega')),
                ('delivery_attempted_at', models.DateTimeField(blank=True, null=True, verbose_name='Tentativa de Entrega')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recipients', to='communication.communicationmessage', verbose_name='Mensagem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Destinatário da Mensagem',
                'verbose_name_plural': 'Destinatários da Mensagem',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MessageResponse',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(verbose_name='Conteúdo da Resposta')),
                ('response_type', models.CharField(choices=[('reply', 'Resposta'), ('acknowledgment', 'Confirmação'), ('question', 'Pergunta'), ('feedback', 'Feedback')], default='reply', max_length=20, verbose_name='Tipo de Resposta')),
                ('is_private', models.BooleanField(default=False, verbose_name='Resposta Privada')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='communication.communicationmessage', verbose_name='Mensagem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='message_responses', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Resposta à Mensagem',
                'verbose_name_plural': 'Respostas às Mensagens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MessageAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='communication/attachments/', verbose_name='Arquivo')),
                ('original_filename', models.CharField(blank=True, max_length=255, verbose_name='Nome Original')),
                ('file_size', models.IntegerField(blank=True, null=True, verbose_name='Tamanho do Arquivo')),
                ('content_type', models.CharField(blank=True, max_length=100, verbose_name='Tipo de Conteúdo')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='Descrição')),
                ('is_public', models.BooleanField(default=True, verbose_name='Público')),
                ('download_count', models.IntegerField(default=0, verbose_name='Downloads')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='communication.communicationmessage', verbose_name='Mensagem')),
                ('uploaded_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Enviado por')),
            ],
            options={
                'verbose_name': 'Anexo da Mensagem',
                'verbose_name_plural': 'Anexos das Mensagens',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CommunicationPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_notifications', models.BooleanField(default=True, verbose_name='Notificações por Email')),
                ('push_notifications', models.BooleanField(default=True, verbose_name='Notificações Push')),
                ('sms_notifications', models.BooleanField(default=False, verbose_name='Notificações SMS')),
                ('notification_frequency', models.CharField(choices=[('immediate', 'Imediata'), ('daily', 'Diária'), ('weekly', 'Semanal'), ('none', 'Nenhuma')], default='immediate', max_length=20, verbose_name='Frequência de Notificação')),
                ('message_types', models.JSONField(default=list, verbose_name='Tipos de Mensagem')),
                ('categories', models.JSONField(default=list, verbose_name='Categorias')),
                ('quiet_hours_start', models.TimeField(blank=True, null=True, verbose_name='Início do Horário Silencioso')),
                ('quiet_hours_end', models.TimeField(blank=True, null=True, verbose_name='Fim do Horário Silencioso')),
                ('language', models.CharField(choices=[('pt', 'Português'), ('en', 'English'), ('es', 'Español')], default='pt', max_length=5, verbose_name='Idioma')),
                ('timezone', models.CharField(default='America/Sao_Paulo', max_length=50, verbose_name='Fuso Horário')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='communication_preferences', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Preferências de Comunicação',
                'verbose_name_plural': 'Preferências de Comunicação',
            },
        ),
        migrations.CreateModel(
            name='CommunicationAnalytics',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metric_name', models.CharField(max_length=100, verbose_name='Nome da Métrica')),
                ('metric_value', models.JSONField(verbose_name='Valor da Métrica')),
                ('period_start', models.DateTimeField(verbose_name='Início do Período')),
                ('period_end', models.DateTimeField(verbose_name='Fim do Período')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('message', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='analytics', to='communication.communicationmessage', verbose_name='Mensagem')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='communication_analytics', to=settings.AUTH_USER_MODEL, verbose_name='Usuário')),
            ],
            options={
                'verbose_name': 'Analítica de Comunicação',
                'verbose_name_plural': 'Analíticas de Comunicação',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='communicationmessage',
            index=models.Index(fields=['status', 'publish_date'], name='communication_msg_status_publish_idx'),
        ),
        migrations.AddIndex(
            model_name='communicationmessage',
            index=models.Index(fields=['author', 'created_at'], name='communication_msg_author_created_idx'),
        ),
        migrations.AddIndex(
            model_name='communicationmessage',
            index=models.Index(fields=['message_type', 'category'], name='communication_msg_type_category_idx'),
        ),
        migrations.AddIndex(
            model_name='messagerecipient',
            index=models.Index(fields=['user', 'is_read'], name='communication_recipient_user_read_idx'),
        ),
        migrations.AddIndex(
            model_name='messagerecipient',
            index=models.Index(fields=['message', 'delivery_status'], name='communication_recipient_msg_delivery_idx'),
        ),
        migrations.AddIndex(
            model_name='messageresponse',
            index=models.Index(fields=['message', 'created_at'], name='communication_response_msg_created_idx'),
        ),
        migrations.AddIndex(
            model_name='messageresponse',
            index=models.Index(fields=['user', 'response_type'], name='communication_response_user_type_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='messagerecipient',
            unique_together={('message', 'user')},
        ),
        migrations.AlterUniqueTogether(
            name='communicationpreferences',
            unique_together={('user',)},
        ),
    ]
