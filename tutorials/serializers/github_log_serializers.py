from rest_framework import serializers
from tutorials.models.webhook import GithubPRLog


class GithubPRLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GithubPRLog
        fields = [
            "id",  # include the model's auto PK
            "pr_number",
            "title",
            "body",
            "pr_url",
            "username",
            "action",
            "state",
            "created_at",
            "url",
        ]
