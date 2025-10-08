from django.db import models

from clients.models import Client


class Manager(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name


class Deal(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Новая"
        WON = "won", "Успех"
        LOST = "lost", "Провал"

    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.NEW,
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="deals",
    )
    manager = models.ForeignKey(
        Manager,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
