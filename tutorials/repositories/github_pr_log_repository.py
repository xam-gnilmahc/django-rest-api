from tutorials.models.webhook import GithubPRLog


class GithubPRLogRepository:
    def exists_by_delivery_id(self, delivery_id):
        return GithubPRLog.objects.filter(delivery_id=delivery_id).exists()

    def create_log(self, data: dict):
        return GithubPRLog.objects.create(**data)
