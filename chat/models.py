from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class ChatChannel(models.Model):
    """Canais de Chat - versão moderna das salas"""
    CHANNEL_TYPES = [
        ('public', 'Público'),
        ('private', 'Privado'),
        ('department', 'Departamento'),
        ('project', 'Projeto'),
        ('task', 'Tarefa'),
        ('direct', 'Mensagem Direta'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Nome do Canal', max_length=100)
    description = models.TextField('Descrição', blank=True)
    channel_type = models.CharField('Tipo', max_length=20, choices=CHANNEL_TYPES, default='public')
    
    # Relacionamentos
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_chat_channels',
        verbose_name='Criado por'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ChatChannelMembership',
        related_name='chat_channels',
        verbose_name='Membros'
    )
    
    # Configurações
    is_active = models.BooleanField('Ativo', default=True)
    is_archived = models.BooleanField('Arquivado', default=False)
    max_members = models.IntegerField('Máximo de Membros', default=100)
    allow_threads = models.BooleanField('Permitir Threads', default=True)
    allow_reactions = models.BooleanField('Permitir Reações', default=True)
    allow_file_sharing = models.BooleanField('Permitir Compartilhamento de Arquivos', default=True)
    
    # Relacionamentos opcionais
    department = models.ForeignKey(
        'hr.Department',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chat_channels',
        verbose_name='Departamento'
    )
    project = models.ForeignKey(
        'projects.Project',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chat_channels',
        verbose_name='Projeto'
    )
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='chat_channels',
        verbose_name='Tarefa'
    )
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Canal de Chat'
        verbose_name_plural = 'Canais de Chat'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_members_count(self):
        return self.members.count()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()

    def get_unread_count(self, user):
        last_read = ChatChannelMembership.objects.filter(
            channel=self, user=user
        ).first()
        
        if last_read and last_read.last_read_at:
            return self.messages.filter(
                created_at__gt=last_read.last_read_at
            ).exclude(sender=user).count()
        
        return self.messages.exclude(sender=user).count()

    def get_online_members(self):
        """Retorna membros online"""
        return self.members.filter(
            last_activity__gte=timezone.now() - timezone.timedelta(minutes=15)
        )


class ChatChannelMembership(models.Model):
    """Associação de usuários com canais de chat"""
    MEMBER_ROLES = [
        ('member', 'Membro'),
        ('admin', 'Administrador'),
        ('moderator', 'Moderador'),
        ('guest', 'Convidado'),
    ]

    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Canal'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='channel_memberships',
        verbose_name='Usuário'
    )
    role = models.CharField('Papel', max_length=20, choices=MEMBER_ROLES, default='member')
    joined_at = models.DateTimeField('Entrou em', auto_now_add=True)
    last_read_at = models.DateTimeField('Última leitura', null=True, blank=True)
    is_muted = models.BooleanField('Silenciado', default=False)
    is_pinned = models.BooleanField('Fixado', default=False)
    notification_level = models.CharField(
        'Nível de Notificação',
        max_length=20,
        choices=[
            ('all', 'Todas'),
            ('mentions', 'Apenas Menções'),
            ('none', 'Nenhuma'),
        ],
        default='all'
    )

    class Meta:
        verbose_name = 'Membro do Canal'
        verbose_name_plural = 'Membros do Canal'
        unique_together = ['channel', 'user']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.channel.name}"

# Manter compatibilidade com salas antigas
ChatRoom = ChatChannel
ChatRoomMembership = ChatChannelMembership


class ChatMessage(models.Model):
    """Mensagens do Chat"""
    MESSAGE_TYPES = [
        ('text', 'Texto'),
        ('file', 'Arquivo'),
        ('image', 'Imagem'),
        ('system', 'Sistema'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Canal',
        null=True,
        blank=True
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Remetente'
    )
    
    # Conteúdo
    content = models.TextField('Mensagem')
    message_type = models.CharField('Tipo', max_length=20, choices=MESSAGE_TYPES, default='text')
    
    # Mensagem de resposta
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='replies',
        verbose_name='Resposta a'
    )
    
    # Arquivo anexo
    attachment = models.FileField('Anexo', upload_to='chat/attachments/', null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    # Status
    is_edited = models.BooleanField('Editado', default=False)
    is_deleted = models.BooleanField('Excluído', default=False)
    
    # Menções
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='mentioned_messages',
        verbose_name='Menções',
        blank=True
    )

    class Meta:
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.get_full_name()} - {self.content[:50]}..."

    def get_attachment_name(self):
        if self.attachment:
            return self.attachment.name.split('/')[-1]
        return None

    def get_attachment_size(self):
        if self.attachment:
            return self.attachment.size
        return 0

    def is_image(self):
        if self.attachment:
            return self.attachment.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'))
        return False

    def get_mentions_list(self):
        return [mention.get_full_name() for mention in self.mentions.all()]


class ChatThread(models.Model):
    """Threads de conversação"""
    parent_message = models.ForeignKey(
        'ChatMessage',
        on_delete=models.CASCADE,
        related_name='thread',
        verbose_name='Mensagem Pai'
    )
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='threads',
        verbose_name='Canal'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_threads',
        verbose_name='Criado por'
    )
    title = models.CharField('Título', max_length=200, blank=True)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Thread'
        verbose_name_plural = 'Threads'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f"Thread da mensagem {self.parent_message.id}"

    def get_message_count(self):
        return self.messages.count()

    def get_last_message(self):
        return self.messages.order_by('-created_at').first()


class ChatReaction(models.Model):
    """Reações às mensagens"""
    REACTION_TYPES = [
        ('👍', 'Curtir'),
        ('👎', 'Não Curtir'),
        ('😄', 'Feliz'),
        ('😢', 'Triste'),
        ('😲', 'Surpreso'),
        ('❤️', 'Coração'),
        ('🚀', 'Foguete'),
        ('👏', 'Palmas'),
        ('🎉', 'Festa'),
        ('✅', 'Concluído'),
    ]

    message = models.ForeignKey(
        'ChatMessage',
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='Mensagem'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_reactions',
        verbose_name='Usuário'
    )
    reaction = models.CharField('Reação', max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Reação'
        verbose_name_plural = 'Reações'
        unique_together = ['message', 'user', 'reaction']

    def __str__(self):
        return f"{self.user.get_full_name()} {self.reaction} {self.message.id}"


class ChatMention(models.Model):
    """Menções em mensagens"""
    message = models.ForeignKey(
        'ChatMessage',
        on_delete=models.CASCADE,
        related_name='message_mentions',
        verbose_name='Mensagem'
    )
    mentioned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_mentions',
        verbose_name='Usuário Mencionado'
    )
    is_read = models.BooleanField('Lido', default=False)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Menção'
        verbose_name_plural = 'Menções'
        unique_together = ['message', 'mentioned_user']

    def __str__(self):
        return f"@{self.mentioned_user.username} na mensagem {self.message.id}"


class ChatIntegration(models.Model):
    """Integrações com outros sistemas"""
    INTEGRATION_TYPES = [
        ('task', 'Tarefas'),
        ('project', 'Projetos'),
        ('calendar', 'Calendário'),
        ('email', 'Email'),
        ('webhook', 'Webhook'),
    ]

    name = models.CharField('Nome', max_length=100)
    integration_type = models.CharField('Tipo', max_length=20, choices=INTEGRATION_TYPES)
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='integrations',
        verbose_name='Canal'
    )
    configuration = models.JSONField('Configuração', default=dict)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_integrations',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Integração'
        verbose_name_plural = 'Integrações'

    def __str__(self):
        return f"{self.name} - {self.channel.name}"


class ChatBot(models.Model):
    """Bots de chat"""
    name = models.CharField('Nome', max_length=100)
    description = models.TextField('Descrição', blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_bot',
        verbose_name='Usuário Bot'
    )
    channels = models.ManyToManyField(
        ChatChannel,
        related_name='bots',
        verbose_name='Canais'
    )
    commands = models.JSONField('Comandos', default=dict)
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_bots',
        verbose_name='Criado por'
    )

    class Meta:
        verbose_name = 'Bot'
        verbose_name_plural = 'Bots'

    def __str__(self):
        return self.name


class ChatAnalytics(models.Model):
    """Analytics do chat"""
    channel = models.ForeignKey(
        ChatChannel,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name='Canal'
    )
    date = models.DateField('Data')
    message_count = models.IntegerField('Mensagens', default=0)
    active_users = models.IntegerField('Usuários Ativos', default=0)
    file_shares = models.IntegerField('Arquivos Compartilhados', default=0)
    reactions_count = models.IntegerField('Reações', default=0)
    thread_count = models.IntegerField('Threads', default=0)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Analytics do Chat'
        verbose_name_plural = 'Analytics do Chat'
        unique_together = ['channel', 'date']

    def __str__(self):
        return f"{self.channel.name} - {self.date}"
