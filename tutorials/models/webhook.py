from django.db import models


class GithubPRLog(models.Model):
    delivery_id = models.CharField(max_length=100, unique=True, null=True)
    pr_number = models.IntegerField()
    title = models.CharField(max_length=512, null=True)
    body = models.TextField(blank=True, null=True)
    pr_url = models.URLField(max_length=1024)
    username = models.CharField(max_length=255)
    action = models.CharField(max_length=50, blank=True, null=True)
    state = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    url = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "webhook_log"
