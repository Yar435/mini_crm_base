from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserSecurityProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="security"
    )
    token_version = models.PositiveIntegerField(default=1)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def _ensure_security_profile(sender, instance, created, **kwargs):
    if created:
        UserSecurityProfile.objects.get_or_create(user=instance)
