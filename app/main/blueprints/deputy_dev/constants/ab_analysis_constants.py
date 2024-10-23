from enum import Enum


class AbAnalysisQueries(Enum):
    approval_query = """
        SELECT
            p.id AS pr_id,
            p.repo_id AS repo_id,
            e.cohort AS cohort,
            EXTRACT(EPOCH FROM (COALESCE(p.scm_approval_time, p.scm_close_time, current_timestamp) - p.scm_creation_time)) AS code_review_time,
            e.human_comment_count AS human_comments,
            p.loc_changed AS lines_of_code,
            r.name AS repo_name,
            p.meta_info->'tokens'->>'pr_diff_tokens' AS pr_diff,
            p.destination_branch,
            p.author_name,
            p.scm_pr_id,
            p.pr_state,
            p.scm_close_time AS pr_close_time
        FROM
            experiments e
        JOIN
            pull_requests p ON e.pr_id = p.id
        JOIN
            repos r ON e.repo_id = r.id
        WHERE
            p.review_status IN ('COMPLETED', 'REJECTED_EXPERIMENT')
            {date_condition}
    """

    merge_query = """
        SELECT
            p.id AS pr_id,
            p.repo_id AS repo_id,
            e.cohort AS cohort,
            COALESCE(
                e.close_time_in_sec,
                EXTRACT(EPOCH FROM (current_timestamp - p.scm_creation_time))
            ) AS code_review_time,
            e.human_comment_count AS human_comments,
            p.loc_changed AS lines_of_code,
            r.name AS repo_name,
            p.meta_info->'tokens'->>'pr_diff_tokens' AS pr_diff,
            p.destination_branch,
            p.author_name,
            p.scm_pr_id,
            p.pr_state,
            p.scm_close_time AS pr_close_time
        FROM
            experiments e
        JOIN
            pull_requests p ON e.pr_id = p.id
        JOIN
            repos r ON e.repo_id = r.id
        WHERE
            p.review_status IN ('COMPLETED', 'REJECTED_EXPERIMENT')
            {date_condition}
    """


class AbAnalysisDates(Enum):
    date_condition_phase1 = "AND e.created_at <= '2024-08-27T18:29'"
    date_condition_phase2 = "AND e.created_at >= '2024-09-02T05:30'"
    date_condition_phase_overall = ""


class AbAnalysisPhases(Enum):
    ab_analysis_phase1 = "phase1"
    ab_analysis_phase2 = "phase2"
    ab_analysis_phase_overall = "overall"
