import uuid
from django.db import models

class GiftConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    box_design = models.CharField(max_length=100)
    video_url = models.URLField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    qr_token = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.qr_token:
            self.qr_token = uuid.uuid4().hex[:16]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"GiftBox {self.box_design} - {self.id}"
