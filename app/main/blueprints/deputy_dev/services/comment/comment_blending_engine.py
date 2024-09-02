from torpedo import CONFIG


class CommentBlendingEngine:
    def __init__(self, llm_comments: dict):
        self.llm_comments = llm_comments
        self.llm_confidence_score_limit = CONFIG.config["AGENT_SETTINGS"]
        self.filtered_comments = []

    def apply_agent_confidence_score_limit(self):
        for agent, data in self.llm_comments.items():

            agent_comments = []
            comments = data.get("response")
            if not comments:
                return
            for comment in comments:
                if comment["confidence_score"] > self.llm_confidence_score_limit[agent]["confidence_score_limit"]:
                    agent_comments.append(comment)

            del data["response"]
            data["comments"] = agent_comments
            return self.llm_comments

    def blend_comments(self):
        # this function can contain other operations in future
        return self.apply_agent_confidence_score_limit()
