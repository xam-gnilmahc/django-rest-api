from typing import Optional, Any, Dict
from tutorials.models.webhook import GithubPRLog


class GithubPRLogRepository:
    def exists_by_delivery_id(self, delivery_id: Optional[str]) -> bool:
        return GithubPRLog.objects.filter(delivery_id=delivery_id).exists()

    def create_log(self, data: Dict[str, Any]) -> GithubPRLog:
        return GithubPRLog.objects.create(**data)
