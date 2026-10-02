from django.db import models
from django.conf import settings
from django.utils import timezone

class TimeStampedModel(models.Model):
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated"
    )

    class Meta:
        abstract = True


class SoftDeleteModel(TimeStampedModel):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted"
    )

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        self.is_deleted = True
        self.deleted_on = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_on", "deleted_by", "updated_on"])

    def restore(self, user=None):
        self.is_deleted = False
        self.deleted_on = None
        self.deleted_by = None
        self.updated_by = user
        self.save(update_fields=["is_deleted", "deleted_on", "deleted_by", "updated_on"])


class UppercaseModel(models.Model):
    """Abstract base model to automatically uppercase all CharField & TextField values."""
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                val = getattr(self, field.name)
                if isinstance(val, str):
                    setattr(self, field.name, val.upper())
        super().save(*args, **kwargs)

