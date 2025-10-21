from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from clients.models import Client
from deals.models import Deal
from deals.models import Manager as DealManager

# какие модели участвуют в RBAC
MODELS = [
    ("clients", "Client"),
    ("deals", "Deal"),
    ("deals", "Manager"),
]

ROLES = {
    "admin": ["view", "add", "change", "delete"],
    "manager": ["view", "add", "change", "delete"],
    "readonly": ["view"],
}


class Command(BaseCommand):
    help = "Create/update default RBAC groups with model permissions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true", help="Clear existing perms before assign."
        )

    def handle(self, *args, **opts):
        groups = {
            "readonly": {
                Client: ["view"],
                Deal: ["view"],
                DealManager: ["view"],
            },
            "manager": {
                # ВАЖНО: add_client здесь!
                Client: ["view", "add", "change"],
                Deal: ["view", "add", "change"],
                DealManager: ["view"],
            },
            "admin": {
                Client: ["view", "add", "change", "delete"],
                Deal: ["view", "add", "change", "delete"],
                DealManager: ["view", "add", "change", "delete"],
            },
        }

        for name, mapping in groups.items():
            group, _ = Group.objects.get_or_create(name=name)
            if opts["reset"]:
                group.permissions.clear()

            for model, actions in mapping.items():
                ct = ContentType.objects.get_for_model(model)
                for action in actions:
                    codename = f"{action}_{model._meta.model_name}"
                    perm = Permission.objects.get(content_type=ct, codename=codename)
                    group.permissions.add(perm)

        self.stdout.write(self.style.SUCCESS("RBAC groups ensured."))
