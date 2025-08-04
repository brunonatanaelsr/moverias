# 🚀 OTIMIZAÇÕES DE PERFORMANCE - MOVE MARIAS

Este arquivo contém sugestões detalhadas de otimização.

## Manager Optimization

### 1. admin.LogEntry

**Problema:** Modelo admin.LogEntry tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class LogEntryOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user', 'content_type')
        return queryset

class LogEntry(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = LogEntryOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 2. auth.Permission

**Problema:** Modelo auth.Permission tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class PermissionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('content_type')
        return queryset

class Permission(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = PermissionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 3. auth.Group

**Problema:** Modelo auth.Group tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class GroupOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('permissions')
        return queryset

class Group(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = GroupOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 4. authtoken.Token

**Problema:** Modelo authtoken.Token tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TokenOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class Token(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TokenOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 5. authtoken.TokenProxy

**Problema:** Modelo authtoken.TokenProxy tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TokenProxyOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class TokenProxy(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TokenProxyOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 6. account.EmailAddress

**Problema:** Modelo account.EmailAddress tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class EmailAddressOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class EmailAddress(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = EmailAddressOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 7. account.EmailConfirmation

**Problema:** Modelo account.EmailConfirmation tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class EmailConfirmationOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('email_address')
        return queryset

class EmailConfirmation(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = EmailConfirmationOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 8. socialaccount.SocialApp

**Problema:** Modelo socialaccount.SocialApp tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SocialAppOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('sites')
        return queryset

class SocialApp(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SocialAppOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 9. socialaccount.SocialAccount

**Problema:** Modelo socialaccount.SocialAccount tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SocialAccountOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class SocialAccount(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SocialAccountOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 10. socialaccount.SocialToken

**Problema:** Modelo socialaccount.SocialToken tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SocialTokenOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('app', 'account')
        return queryset

class SocialToken(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SocialTokenOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 11. otp_totp.TOTPDevice

**Problema:** Modelo otp_totp.TOTPDevice tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TOTPDeviceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class TOTPDevice(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TOTPDeviceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 12. users.CustomUser

**Problema:** Modelo users.CustomUser tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CustomUserOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('groups', 'user_permissions')
        return queryset

class CustomUser(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CustomUserOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 13. users.UserProfile

**Problema:** Modelo users.UserProfile tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class UserProfileOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class UserProfile(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = UserProfileOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 14. users.UserActivity

**Problema:** Modelo users.UserActivity tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class UserActivityOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class UserActivity(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = UserActivityOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 15. users.SystemRole

**Problema:** Modelo users.SystemRole tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SystemRoleOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('permissions')
        return queryset

class SystemRole(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SystemRoleOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 16. core.SystemLog

**Problema:** Modelo core.SystemLog tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SystemLogOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class SystemLog(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SystemLogOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 17. core.FileUpload

**Problema:** Modelo core.FileUpload tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class FileUploadOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('uploaded_by')
        return queryset

class FileUpload(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = FileUploadOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 18. members.Consent

**Problema:** Modelo members.Consent tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ConsentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('beneficiary')
        return queryset

class Consent(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ConsentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 19. social.FamilyMember

**Problema:** Modelo social.FamilyMember tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class FamilyMemberOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('anamnesis')
        return queryset

class FamilyMember(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = FamilyMemberOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 20. social.IdentifiedVulnerability

**Problema:** Modelo social.IdentifiedVulnerability tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class IdentifiedVulnerabilityOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('anamnesis', 'category')
        return queryset

class IdentifiedVulnerability(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = IdentifiedVulnerabilityOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 21. social.SocialAnamnesisEvolution

**Problema:** Modelo social.SocialAnamnesisEvolution tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SocialAnamnesisEvolutionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('anamnesis', 'created_by')
        return queryset

class SocialAnamnesisEvolution(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SocialAnamnesisEvolutionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 22. projects.ProjectSession

**Problema:** Modelo projects.ProjectSession tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectSessionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('project')
        return queryset

class ProjectSession(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectSessionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 23. projects.ProjectAttendance

**Problema:** Modelo projects.ProjectAttendance tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectAttendanceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('session', 'enrollment')
        return queryset

class ProjectAttendance(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectAttendanceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 24. projects.ProjectEvaluation

**Problema:** Modelo projects.ProjectEvaluation tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectEvaluationOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('enrollment', 'session')
        return queryset

class ProjectEvaluation(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectEvaluationOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 25. projects.ProjectResource

**Problema:** Modelo projects.ProjectResource tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectResourceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('project')
        return queryset

class ProjectResource(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectResourceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 26. projects.ProjectEnrollment

**Problema:** Modelo projects.ProjectEnrollment tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectEnrollmentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('beneficiary', 'project')
        return queryset

class ProjectEnrollment(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectEnrollmentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 27. projects.ProjectMilestone

**Problema:** Modelo projects.ProjectMilestone tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectMilestoneOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('project')
        return queryset

class ProjectMilestone(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectMilestoneOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 28. projects.ProjectReport

**Problema:** Modelo projects.ProjectReport tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectReportOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('project')
        return queryset

class ProjectReport(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectReportOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 29. projects.ProjectBudget

**Problema:** Modelo projects.ProjectBudget tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ProjectBudgetOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('project')
        return queryset

class ProjectBudget(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ProjectBudgetOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 30. coaching.ActionPlan

**Problema:** Modelo coaching.ActionPlan tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ActionPlanOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('beneficiary')
        return queryset

class ActionPlan(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ActionPlanOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 31. coaching.WheelOfLife

**Problema:** Modelo coaching.WheelOfLife tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class WheelOfLifeOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('beneficiary')
        return queryset

class WheelOfLife(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = WheelOfLifeOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 32. workshops.WorkshopSession

**Problema:** Modelo workshops.WorkshopSession tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class WorkshopSessionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('workshop')
        return queryset

class WorkshopSession(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = WorkshopSessionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 33. workshops.WorkshopEnrollment

**Problema:** Modelo workshops.WorkshopEnrollment tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class WorkshopEnrollmentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('workshop', 'beneficiary')
        return queryset

class WorkshopEnrollment(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = WorkshopEnrollmentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 34. workshops.SessionAttendance

**Problema:** Modelo workshops.SessionAttendance tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SessionAttendanceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('session', 'enrollment')
        return queryset

class SessionAttendance(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SessionAttendanceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 35. workshops.WorkshopEvaluation

**Problema:** Modelo workshops.WorkshopEvaluation tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class WorkshopEvaluationOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('enrollment')
        return queryset

class WorkshopEvaluation(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = WorkshopEvaluationOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 36. certificates.Certificate

**Problema:** Modelo certificates.Certificate tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CertificateOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('member', 'workshop', 'template')
        return queryset

class Certificate(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CertificateOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 37. certificates.CertificateRequest

**Problema:** Modelo certificates.CertificateRequest tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CertificateRequestOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('member', 'workshop', 'certificate')
        return queryset

class CertificateRequest(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CertificateRequestOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 38. certificates.CertificateDelivery

**Problema:** Modelo certificates.CertificateDelivery tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CertificateDeliveryOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('certificate')
        return queryset

class CertificateDelivery(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CertificateDeliveryOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 39. notifications.NotificationTemplate

**Problema:** Modelo notifications.NotificationTemplate tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class NotificationTemplateOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('channel')
        return queryset

class NotificationTemplate(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = NotificationTemplateOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 40. notifications.Notification

**Problema:** Modelo notifications.Notification tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class NotificationOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('recipient', 'channel', 'content_type')
        return queryset

class Notification(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = NotificationOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 41. notifications.NotificationPreference

**Problema:** Modelo notifications.NotificationPreference tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class NotificationPreferenceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class NotificationPreference(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = NotificationPreferenceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 42. notifications.NotificationBatch

**Problema:** Modelo notifications.NotificationBatch tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class NotificationBatchOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('template')
        queryset = queryset.prefetch_related('target_users')
        return queryset

class NotificationBatch(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = NotificationBatchOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 43. hr.Department

**Problema:** Modelo hr.Department tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class DepartmentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('manager')
        return queryset

class Department(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = DepartmentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 44. hr.JobPosition

**Problema:** Modelo hr.JobPosition tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class JobPositionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('department')
        return queryset

class JobPosition(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = JobPositionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 45. hr.Employee

**Problema:** Modelo hr.Employee tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class EmployeeOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user', 'job_position', 'department', 'direct_supervisor', 'created_by')
        return queryset

class Employee(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = EmployeeOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 46. hr.EmployeeDocument

**Problema:** Modelo hr.EmployeeDocument tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class EmployeeDocumentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('employee', 'uploaded_by')
        return queryset

class EmployeeDocument(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = EmployeeDocumentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 47. hr.PerformanceReview

**Problema:** Modelo hr.PerformanceReview tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class PerformanceReviewOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('employee', 'reviewed_by')
        return queryset

class PerformanceReview(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = PerformanceReviewOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 48. hr.TrainingRecord

**Problema:** Modelo hr.TrainingRecord tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TrainingRecordOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('employee', 'created_by')
        return queryset

class TrainingRecord(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TrainingRecordOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 49. hr.OnboardingProgram

**Problema:** Modelo hr.OnboardingProgram tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class OnboardingProgramOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('department', 'responsible_user')
        return queryset

class OnboardingProgram(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = OnboardingProgramOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 50. hr.OnboardingTask

**Problema:** Modelo hr.OnboardingTask tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class OnboardingTaskOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('program', 'responsible_user')
        return queryset

class OnboardingTask(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = OnboardingTaskOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 51. hr.OnboardingInstance

**Problema:** Modelo hr.OnboardingInstance tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class OnboardingInstanceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('employee', 'program', 'mentor')
        return queryset

class OnboardingInstance(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = OnboardingInstanceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 52. hr.OnboardingTaskCompletion

**Problema:** Modelo hr.OnboardingTaskCompletion tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class OnboardingTaskCompletionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('instance', 'task', 'completed_by')
        return queryset

class OnboardingTaskCompletion(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = OnboardingTaskCompletionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 53. hr.Goal

**Problema:** Modelo hr.Goal tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class GoalOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('owner', 'created_by')
        queryset = queryset.prefetch_related('collaborators')
        return queryset

class Goal(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = GoalOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 54. hr.Feedback

**Problema:** Modelo hr.Feedback tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class FeedbackOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('from_user', 'to_user')
        return queryset

class Feedback(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = FeedbackOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 55. hr.AdvancedTraining

**Problema:** Modelo hr.AdvancedTraining tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class AdvancedTrainingOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('created_by')
        return queryset

class AdvancedTraining(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = AdvancedTrainingOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 56. hr.TrainingRegistration

**Problema:** Modelo hr.TrainingRegistration tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TrainingRegistrationOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('training', 'employee', 'approved_by')
        return queryset

class TrainingRegistration(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TrainingRegistrationOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 57. hr.HRAnalytics

**Problema:** Modelo hr.HRAnalytics tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class HRAnalyticsOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('department', 'created_by')
        return queryset

class HRAnalytics(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = HRAnalyticsOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 58. tasks.TaskBoard

**Problema:** Modelo tasks.TaskBoard tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskBoardOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('department', 'owner')
        queryset = queryset.prefetch_related('members')
        return queryset

class TaskBoard(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskBoardOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 59. tasks.TaskColumn

**Problema:** Modelo tasks.TaskColumn tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskColumnOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('board')
        return queryset

class TaskColumn(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskColumnOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 60. tasks.TaskTemplate

**Problema:** Modelo tasks.TaskTemplate tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskTemplateOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('department', 'created_by')
        return queryset

class TaskTemplate(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskTemplateOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 61. tasks.TaskAutomation

**Problema:** Modelo tasks.TaskAutomation tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskAutomationOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('board', 'created_by')
        return queryset

class TaskAutomation(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskAutomationOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 62. tasks.Task

**Problema:** Modelo tasks.Task tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('board', 'column', 'assignee', 'reporter')
        return queryset

class Task(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 63. tasks.TaskComment

**Problema:** Modelo tasks.TaskComment tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskCommentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('task', 'author')
        return queryset

class TaskComment(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskCommentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 64. tasks.TaskAttachment

**Problema:** Modelo tasks.TaskAttachment tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskAttachmentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('task', 'uploaded_by')
        return queryset

class TaskAttachment(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskAttachmentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 65. tasks.TaskActivity

**Problema:** Modelo tasks.TaskActivity tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskActivityOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('task', 'user')
        return queryset

class TaskActivity(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskActivityOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 66. tasks.TaskTimeEntry

**Problema:** Modelo tasks.TaskTimeEntry tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskTimeEntryOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('task', 'user')
        return queryset

class TaskTimeEntry(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskTimeEntryOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 67. tasks.TaskDependency

**Problema:** Modelo tasks.TaskDependency tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskDependencyOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('task', 'depends_on', 'created_by')
        return queryset

class TaskDependency(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskDependencyOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 68. tasks.TaskLabel

**Problema:** Modelo tasks.TaskLabel tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskLabelOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('board')
        return queryset

class TaskLabel(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskLabelOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 69. tasks.TaskRecurrence

**Problema:** Modelo tasks.TaskRecurrence tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class TaskRecurrenceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('task_template', 'board')
        return queryset

class TaskRecurrence(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = TaskRecurrenceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 70. chat.ChatChannel

**Problema:** Modelo chat.ChatChannel tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatChannelOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('created_by', 'department', 'project', 'task')
        queryset = queryset.prefetch_related('members')
        return queryset

class ChatChannel(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatChannelOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 71. chat.ChatChannelMembership

**Problema:** Modelo chat.ChatChannelMembership tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatChannelMembershipOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('channel', 'user')
        return queryset

class ChatChannelMembership(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatChannelMembershipOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 72. chat.ChatMessage

**Problema:** Modelo chat.ChatMessage tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatMessageOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('channel', 'sender', 'reply_to')
        queryset = queryset.prefetch_related('mentions')
        return queryset

class ChatMessage(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatMessageOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 73. chat.ChatThread

**Problema:** Modelo chat.ChatThread tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatThreadOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('parent_message', 'channel', 'created_by')
        return queryset

class ChatThread(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatThreadOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 74. chat.ChatReaction

**Problema:** Modelo chat.ChatReaction tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatReactionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('message', 'user')
        return queryset

class ChatReaction(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatReactionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 75. chat.ChatMention

**Problema:** Modelo chat.ChatMention tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatMentionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('message', 'mentioned_user')
        return queryset

class ChatMention(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatMentionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 76. chat.ChatIntegration

**Problema:** Modelo chat.ChatIntegration tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatIntegrationOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('channel', 'created_by')
        return queryset

class ChatIntegration(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatIntegrationOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 77. chat.ChatBot

**Problema:** Modelo chat.ChatBot tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatBotOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user', 'created_by')
        queryset = queryset.prefetch_related('channels')
        return queryset

class ChatBot(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatBotOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 78. chat.ChatAnalytics

**Problema:** Modelo chat.ChatAnalytics tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ChatAnalyticsOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('channel')
        return queryset

class ChatAnalytics(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ChatAnalyticsOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 79. communication.Announcement

**Problema:** Modelo communication.Announcement tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class AnnouncementOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author')
        queryset = queryset.prefetch_related('departments', 'target_users')
        return queryset

class Announcement(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = AnnouncementOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 80. communication.AnnouncementAttachment

**Problema:** Modelo communication.AnnouncementAttachment tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class AnnouncementAttachmentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('announcement')
        return queryset

class AnnouncementAttachment(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = AnnouncementAttachmentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 81. communication.AnnouncementReadReceipt

**Problema:** Modelo communication.AnnouncementReadReceipt tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class AnnouncementReadReceiptOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('announcement', 'user')
        return queryset

class AnnouncementReadReceipt(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = AnnouncementReadReceiptOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 82. communication.InternalMemo

**Problema:** Modelo communication.InternalMemo tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class InternalMemoOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('from_user', 'from_department')
        queryset = queryset.prefetch_related('to_users', 'to_departments')
        return queryset

class InternalMemo(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = InternalMemoOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 83. communication.MemoResponse

**Problema:** Modelo communication.MemoResponse tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class MemoResponseOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('memo', 'user')
        return queryset

class MemoResponse(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = MemoResponseOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 84. communication.Newsletter

**Problema:** Modelo communication.Newsletter tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class NewsletterOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author')
        return queryset

class Newsletter(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = NewsletterOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 85. communication.SuggestionBox

**Problema:** Modelo communication.SuggestionBox tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class SuggestionBoxOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author', 'department', 'assigned_to', 'responded_by')
        return queryset

class SuggestionBox(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = SuggestionBoxOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 86. communication.CommunicationSettings

**Problema:** Modelo communication.CommunicationSettings tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationSettingsOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class CommunicationSettings(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationSettingsOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 87. communication.CommunicationCampaign

**Problema:** Modelo communication.CommunicationCampaign tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationCampaignOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('created_by')
        queryset = queryset.prefetch_related('target_departments', 'target_users')
        return queryset

class CommunicationCampaign(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationCampaignOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 88. communication.CommunicationTemplate

**Problema:** Modelo communication.CommunicationTemplate tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationTemplateOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('created_by')
        return queryset

class CommunicationTemplate(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationTemplateOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 89. communication.CommunicationChannel

**Problema:** Modelo communication.CommunicationChannel tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationChannelOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('created_by')
        return queryset

class CommunicationChannel(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationChannelOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 90. communication.CommunicationSegment

**Problema:** Modelo communication.CommunicationSegment tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationSegmentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('created_by')
        queryset = queryset.prefetch_related('users')
        return queryset

class CommunicationSegment(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationSegmentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 91. communication.CommunicationAnalytics

**Problema:** Modelo communication.CommunicationAnalytics tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationAnalyticsOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('campaign')
        return queryset

class CommunicationAnalytics(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationAnalyticsOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 92. communication.CommunicationEvent

**Problema:** Modelo communication.CommunicationEvent tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationEventOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('campaign', 'user')
        return queryset

class CommunicationEvent(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationEventOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 93. communication.CommunicationPreference

**Problema:** Modelo communication.CommunicationPreference tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationPreferenceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class CommunicationPreference(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationPreferenceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 94. communication.CommunicationMessage

**Problema:** Modelo communication.CommunicationMessage tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationMessageOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('author', 'content_type')
        return queryset

class CommunicationMessage(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationMessageOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 95. communication.MessageRecipient

**Problema:** Modelo communication.MessageRecipient tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class MessageRecipientOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('message', 'user')
        return queryset

class MessageRecipient(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = MessageRecipientOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 96. communication.MessageResponse

**Problema:** Modelo communication.MessageResponse tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class MessageResponseOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('message', 'user')
        return queryset

class MessageResponse(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = MessageResponseOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 97. communication.MessageAttachment

**Problema:** Modelo communication.MessageAttachment tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class MessageAttachmentOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('message', 'uploaded_by')
        return queryset

class MessageAttachment(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = MessageAttachmentOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 98. communication.CommunicationPreferences

**Problema:** Modelo communication.CommunicationPreferences tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationPreferencesOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('user')
        return queryset

class CommunicationPreferences(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationPreferencesOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 99. communication.CommunicationAnalyticsRefactored

**Problema:** Modelo communication.CommunicationAnalyticsRefactored tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class CommunicationAnalyticsRefactoredOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('message', 'user')
        return queryset

class CommunicationAnalyticsRefactored(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = CommunicationAnalyticsRefactoredOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 100. activities.BeneficiaryActivity

**Problema:** Modelo activities.BeneficiaryActivity tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class BeneficiaryActivityOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('beneficiary', 'social_anamnesis', 'created_by')
        return queryset

class BeneficiaryActivity(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = BeneficiaryActivityOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 101. activities.ActivitySession

**Problema:** Modelo activities.ActivitySession tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ActivitySessionOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('activity')
        return queryset

class ActivitySession(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ActivitySessionOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 102. activities.ActivityAttendance

**Problema:** Modelo activities.ActivityAttendance tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ActivityAttendanceOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('session', 'recorded_by')
        return queryset

class ActivityAttendance(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ActivityAttendanceOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 103. activities.ActivityFeedback

**Problema:** Modelo activities.ActivityFeedback tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ActivityFeedbackOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('activity')
        return queryset

class ActivityFeedback(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ActivityFeedbackOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

### 104. activities.ActivityNote

**Problema:** Modelo activities.ActivityNote tem relacionamentos mas não tem manager otimizado

**Solução:** Adicionar manager com select_related/prefetch_related

**Prioridade:** MÉDIO

**Código sugerido:**

```python

class ActivityNoteOptimizedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('activity', 'created_by')
        return queryset

class ActivityNote(models.Model):
    # ... campos existentes ...
    
    objects = models.Manager()
    optimized_objects = ActivityNoteOptimizedManager()
    
    class Meta:
        # ... Meta existente ...

```

---

## Database Index

### 1. auth.Permission

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 2. auth.Group

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 3. sites.Site

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 4. account.EmailAddress

**Problema:** Campo comum email sem índice

**Solução:** Adicionar db_index=True no campo email

**Prioridade:** MÉDIO

---

### 5. socialaccount.SocialApp

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 6. otp_totp.TOTPDevice

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 7. users.CustomUser

**Problema:** Campo comum email sem índice

**Solução:** Adicionar db_index=True no campo email

**Prioridade:** MÉDIO

---

### 8. users.CustomUser

**Problema:** Campo comum full_name sem índice

**Solução:** Adicionar db_index=True no campo full_name

**Prioridade:** MÉDIO

---

### 9. users.CustomUser

**Problema:** Campo comum phone sem índice

**Solução:** Adicionar db_index=True no campo phone

**Prioridade:** MÉDIO

---

### 10. users.CustomUser

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 11. users.CustomUser

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 12. users.SystemRole

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 13. users.SystemRole

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 14. core.SystemConfig

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 15. core.SystemConfig

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 16. core.FileUpload

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 17. members.Beneficiary

**Problema:** Campo comum full_name sem índice

**Solução:** Adicionar db_index=True no campo full_name

**Prioridade:** MÉDIO

---

### 18. members.Beneficiary

**Problema:** Campo comum email sem índice

**Solução:** Adicionar db_index=True no campo email

**Prioridade:** MÉDIO

---

### 19. members.Beneficiary

**Problema:** Campo comum cpf sem índice

**Solução:** Adicionar db_index=True no campo cpf

**Prioridade:** MÉDIO

---

### 20. members.Beneficiary

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 21. members.Beneficiary

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 22. social.SocialAnamnesis

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 23. social.SocialAnamnesis

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 24. social.SocialAnamnesis

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 25. social.FamilyMember

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 26. social.FamilyMember

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 27. social.FamilyMember

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 28. social.VulnerabilityCategory

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 29. social.VulnerabilityCategory

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 30. social.VulnerabilityCategory

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 31. social.IdentifiedVulnerability

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 32. social.IdentifiedVulnerability

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 33. social.IdentifiedVulnerability

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 34. social.SocialAnamnesisEvolution

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 35. projects.Project

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 36. projects.Project

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 37. projects.Project

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 38. projects.Project

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 39. projects.Project

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 40. projects.ProjectSession

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 41. projects.ProjectAttendance

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 42. projects.ProjectAttendance

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 43. projects.ProjectResource

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 44. projects.ProjectResource

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 45. projects.ProjectEnrollment

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 46. projects.ProjectEnrollment

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 47. projects.ProjectMilestone

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 48. projects.ProjectMilestone

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 49. projects.ProjectMilestone

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 50. projects.ProjectReport

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 51. projects.ProjectBudget

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 52. coaching.ActionPlan

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 53. coaching.ActionPlan

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 54. coaching.WheelOfLife

**Problema:** Campo comum date sem índice

**Solução:** Adicionar db_index=True no campo date

**Prioridade:** MÉDIO

---

### 55. coaching.WheelOfLife

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 56. evolution.EvolutionRecord

**Problema:** Campo comum date sem índice

**Solução:** Adicionar db_index=True no campo date

**Prioridade:** MÉDIO

---

### 57. evolution.EvolutionRecord

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 58. evolution.EvolutionRecord

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 59. workshops.Workshop

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 60. workshops.Workshop

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 61. workshops.Workshop

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 62. workshops.Workshop

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 63. workshops.Workshop

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 64. workshops.WorkshopSession

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 65. workshops.WorkshopEnrollment

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 66. workshops.WorkshopEnrollment

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 67. workshops.SessionAttendance

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 68. workshops.WorkshopEvaluation

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 69. certificates.CertificateTemplate

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 70. certificates.CertificateTemplate

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 71. certificates.CertificateTemplate

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 72. certificates.Certificate

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 73. certificates.Certificate

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 74. certificates.Certificate

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 75. certificates.Certificate

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 76. notifications.NotificationChannel

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 77. notifications.NotificationTemplate

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 78. notifications.NotificationTemplate

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 79. notifications.NotificationTemplate

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 80. notifications.Notification

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 81. notifications.Notification

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 82. notifications.Notification

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 83. notifications.NotificationPreference

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 84. notifications.NotificationPreference

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 85. notifications.NotificationBatch

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 86. notifications.NotificationBatch

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 87. notifications.NotificationBatch

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 88. notifications.NotificationBatch

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 89. notifications.NotificationBatch

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 90. hr.Department

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 91. hr.Department

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 92. hr.Department

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 93. hr.JobPosition

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 94. hr.JobPosition

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 95. hr.JobPosition

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 96. hr.Employee

**Problema:** Campo comum full_name sem índice

**Solução:** Adicionar db_index=True no campo full_name

**Prioridade:** MÉDIO

---

### 97. hr.Employee

**Problema:** Campo comum cpf sem índice

**Solução:** Adicionar db_index=True no campo cpf

**Prioridade:** MÉDIO

---

### 98. hr.Employee

**Problema:** Campo comum phone sem índice

**Solução:** Adicionar db_index=True no campo phone

**Prioridade:** MÉDIO

---

### 99. hr.Employee

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 100. hr.Employee

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 101. hr.EmployeeDocument

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 102. hr.PerformanceReview

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 103. hr.PerformanceReview

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 104. hr.TrainingRecord

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 105. hr.TrainingRecord

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 106. hr.TrainingRecord

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 107. hr.OnboardingProgram

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 108. hr.OnboardingProgram

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 109. hr.OnboardingProgram

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 110. hr.OnboardingProgram

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 111. hr.OnboardingTask

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 112. hr.OnboardingTask

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 113. hr.OnboardingInstance

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 114. hr.OnboardingInstance

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 115. hr.OnboardingInstance

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 116. hr.OnboardingInstance

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 117. hr.Goal

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 118. hr.Goal

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 119. hr.Goal

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 120. hr.Goal

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 121. hr.Goal

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 122. hr.Feedback

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 123. hr.AdvancedTraining

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 124. hr.AdvancedTraining

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 125. hr.AdvancedTraining

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 126. hr.AdvancedTraining

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 127. hr.AdvancedTraining

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 128. hr.TrainingRegistration

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 129. hr.HRAnalytics

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 130. tasks.TaskBoard

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 131. tasks.TaskBoard

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 132. tasks.TaskBoard

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 133. tasks.TaskColumn

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 134. tasks.TaskColumn

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 135. tasks.TaskTemplate

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 136. tasks.TaskTemplate

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 137. tasks.TaskAutomation

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 138. tasks.TaskAutomation

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 139. tasks.Task

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 140. tasks.Task

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 141. tasks.Task

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 142. tasks.Task

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 143. tasks.TaskComment

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 144. tasks.TaskComment

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 145. tasks.TaskAttachment

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 146. tasks.TaskActivity

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 147. tasks.TaskTimeEntry

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 148. tasks.TaskDependency

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 149. tasks.TaskLabel

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 150. tasks.TaskLabel

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 151. tasks.TaskRecurrence

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 152. tasks.TaskRecurrence

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 153. chat.ChatChannel

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 154. chat.ChatChannel

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 155. chat.ChatChannel

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 156. chat.ChatMessage

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 157. chat.ChatMessage

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 158. chat.ChatThread

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 159. chat.ChatThread

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 160. chat.ChatThread

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 161. chat.ChatReaction

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 162. chat.ChatMention

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 163. chat.ChatIntegration

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 164. chat.ChatIntegration

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 165. chat.ChatBot

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 166. chat.ChatBot

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 167. chat.ChatAnalytics

**Problema:** Campo comum date sem índice

**Solução:** Adicionar db_index=True no campo date

**Prioridade:** MÉDIO

---

### 168. chat.ChatAnalytics

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 169. communication.Announcement

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 170. communication.Announcement

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 171. communication.Announcement

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 172. communication.AnnouncementAttachment

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 173. communication.InternalMemo

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 174. communication.InternalMemo

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 175. communication.InternalMemo

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 176. communication.MemoResponse

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 177. communication.Newsletter

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 178. communication.Newsletter

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 179. communication.Newsletter

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 180. communication.SuggestionBox

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 181. communication.SuggestionBox

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 182. communication.SuggestionBox

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 183. communication.SuggestionBox

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 184. communication.CommunicationSettings

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 185. communication.CommunicationSettings

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 186. communication.CommunicationCampaign

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 187. communication.CommunicationCampaign

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 188. communication.CommunicationCampaign

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 189. communication.CommunicationCampaign

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 190. communication.CommunicationTemplate

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 191. communication.CommunicationTemplate

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 192. communication.CommunicationTemplate

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 193. communication.CommunicationChannel

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 194. communication.CommunicationChannel

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 195. communication.CommunicationChannel

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 196. communication.CommunicationSegment

**Problema:** Campo comum name sem índice

**Solução:** Adicionar db_index=True no campo name

**Prioridade:** MÉDIO

---

### 197. communication.CommunicationSegment

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 198. communication.CommunicationSegment

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 199. communication.CommunicationAnalytics

**Problema:** Campo comum date sem índice

**Solução:** Adicionar db_index=True no campo date

**Prioridade:** MÉDIO

---

### 200. communication.CommunicationAnalytics

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 201. communication.CommunicationPreference

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 202. communication.CommunicationPreference

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 203. communication.CommunicationMessage

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 204. communication.CommunicationMessage

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 205. communication.CommunicationMessage

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 206. communication.CommunicationMessage

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 207. communication.MessageRecipient

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 208. communication.MessageResponse

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 209. communication.MessageResponse

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 210. communication.MessageAttachment

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 211. communication.CommunicationPreferences

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 212. communication.CommunicationPreferences

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 213. communication.CommunicationAnalyticsRefactored

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 214. activities.BeneficiaryActivity

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 215. activities.BeneficiaryActivity

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 216. activities.BeneficiaryActivity

**Problema:** Campo comum start_date sem índice

**Solução:** Adicionar db_index=True no campo start_date

**Prioridade:** MÉDIO

---

### 217. activities.BeneficiaryActivity

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 218. activities.BeneficiaryActivity

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 219. activities.ActivitySession

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 220. activities.ActivitySession

**Problema:** Campo comum status sem índice

**Solução:** Adicionar db_index=True no campo status

**Prioridade:** MÉDIO

---

### 221. activities.ActivitySession

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 222. activities.ActivitySession

**Problema:** Campo comum updated_at sem índice

**Solução:** Adicionar db_index=True no campo updated_at

**Prioridade:** MÉDIO

---

### 223. activities.ActivityFeedback

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

### 224. activities.ActivityNote

**Problema:** Campo comum title sem índice

**Solução:** Adicionar db_index=True no campo title

**Prioridade:** MÉDIO

---

### 225. activities.ActivityNote

**Problema:** Campo comum created_at sem índice

**Solução:** Adicionar db_index=True no campo created_at

**Prioridade:** MÉDIO

---

