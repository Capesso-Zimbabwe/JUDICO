from django.db import models

# You can add custom admin models here if needed
# For example, admin settings, logs, etc.

class AdminSettings(models.Model):
    site_title = models.CharField(max_length=100, default="JUDICO Admin")
    site_header = models.CharField(max_length=100, default="JUDICO Administration")
    site_url = models.CharField(max_length=100, default="/")
    
    def __str__(self):
        return self.site_title
