from app.main.blueprints.deputy_dev.services.repository.extension_comments.repository import ExtensionCommentRepository
class ExtensionReviewPostProcessor:
    async def post_process_pr(self, data, user_team_id: int):
        review_id = data.get("review_id")
        comments = await ExtensionCommentRepository().get_review_comments(review_id)

        # comments = fetch_comments(review_id)
        # pr_diff = fetch_pr_diff(review_id)


    def fetch_comments(self, review_id):
        pass



