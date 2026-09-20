from django.db import models
from django.core.cache import cache

class SiteConfiguration(models.Model):
    enable_ai_insights = models.BooleanField(default=False, help_text="Enable AI generated insights on product detail pages.")

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete('site_config')

    def delete(self, *args, **kwargs):
        pass # Prevent deletion

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Site Configuration"
