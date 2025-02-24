from enum import Enum


class GraphTypes(Enum):
    COMMENT_BUCKET_TYPES = "comment_bucket_types"
    PR_SCORE = "pr_score"
    REVIEWED_VS_REJECTED = "reviewed_vs_rejected"


class StatusTypes(Enum):
    PULL_REQUEST_STATUS = "COMPLETED"
    BUCKET_STATUS = "active"


class TileTypes(Enum):
    NUM_OF_MERGED_PRS = "num_of_merged_prs"
    NUM_OF_RAISED_PRS = "num_of_raised_prs"
    CODE_REVIEW_TIME = "code_review_time"


class AnalyticsDataQueries(Enum):
    comment_bucket_types_query = """
        SELECT
            a.agent_name AS bucket_type,
            count(*) AS count
        FROM
            agent_comment_mappings acm
        JOIN
            agents a ON acm.agent_id = a.id
        JOIN
            pr_comments prc ON acm.pr_comment_id = prc.id
        JOIN
            pull_requests pr ON prc.pr_id = pr.id
        WHERE
            prc.created_at >= '{start_date}'
            AND prc.created_at <= '{end_date}'
            AND prc.repo_id in ({repo_ids})
            AND pr.iteration = 1
        GROUP BY
            a.agent_name
        ORDER BY
            count DESC
    """

    pr_score_query = """
        WITH time_intervals AS (
            SELECT
                generate_series(
                    date_trunc('{interval_time}', '{start_date}'::timestamp),
                    date_trunc('{interval_time}', '{end_date}'::timestamp),
                    '{interval_filter}'::interval
                ) AS step
        ),
        aggregated_data AS (
            SELECT
                date_trunc('{interval_time}', '{start_date}'::timestamp) +
                floor(extract(epoch from created_at - date_trunc('{interval_time}', '{start_date}'::timestamp)) /
                    extract(epoch from '{interval_filter}'::interval)) * '{interval_filter}'::interval AS step,
                AVG(quality_score) AS pr_score
            FROM
                pull_requests
            WHERE
                created_at >= '{start_date}'
                AND created_at <= '{end_date}'
                AND review_status = '{pull_request_status}'
                AND repo_id in ({repo_ids})
                AND iteration = 1
            GROUP BY
                step
        )
        SELECT
            ti.step,
            COALESCE(ad.pr_score, 0) AS pr_score
        FROM
            time_intervals ti
        LEFT JOIN
            aggregated_data ad ON ti.step = ad.step
        ORDER BY
            ti.step;
    """

    reviewed_vs_rejected_query = """
        WITH time_intervals AS (
            SELECT
                generate_series(
                    date_trunc('{interval_time}', '{start_date}'::timestamp),
                    date_trunc('{interval_time}', '{end_date}'::timestamp),
                    '{interval_filter}'::interval
                ) AS step
        ),
        aggregated_data AS (
            SELECT
                date_trunc('{interval_time}', '{start_date}'::timestamp) +
                floor(extract(epoch from created_at - date_trunc('{interval_time}', '{start_date}'::timestamp)) /
                    extract(epoch from '{interval_filter}'::interval)) * '{interval_filter}'::interval AS step,
                review_status,
                COUNT(*) AS count
            FROM
                pull_requests
            WHERE
                created_at >= '{start_date}'
                AND created_at <= '{end_date}'
                AND repo_id in ({repo_ids})
                AND iteration = 1
            GROUP BY
                step, review_status
        )
        SELECT
            ti.step,
            COALESCE(ad.count, 0) AS count,
            COALESCE(ad.review_status, 'UNKNOWN') AS review_status
        FROM
            time_intervals ti
        LEFT JOIN
            aggregated_data ad ON ti.step = ad.step
        ORDER BY
            ti.step;
    """


class DashboardQueries(Enum):
    teams_query = """
        SELECT DISTINCT
            t.id,
            u.org_name as name
        FROM
            teams t
        JOIN
            user_teams ut on t.id = ut.team_id
        JOIN
            users u on u.id = ut.user_id
        WHERE
            t.id in (1,3,4)
        ORDER BY
            t.id
    """

    workspaces_query = """
        SELECT
            id,
            name,
            scm
        FROM
            workspaces
        WHERE
            team_id = {team_id_condition}
        ORDER BY
            id
    """

    repos_query = """
        SELECT
            id,
            name
        FROM
            repos
        WHERE
            workspace_id = {workspace_id_condition}
        ORDER BY
            id
    """

    pull_requests_query = """
        SELECT
            prc.scm,
            w.name as workspace_name,
            r.name as repo_name,
            pr.scm_pr_id,
            prc.scm_comment_id,
            pr.title as pr_title
        FROM
            comment_bucket_mapping cbm
        JOIN
            buckets b ON cbm.bucket_id = b.id
        JOIN
            pr_comments prc ON cbm.pr_comment_id = prc.id
        JOIN
            repos r on r.id = prc.repo_id
        JOIN
            pull_requests pr ON prc.pr_id = pr.id
        JOIN
            workspaces w on w.id = prc.workspace_id
        WHERE
            prc.created_at >= '{start_date}'
            AND prc.created_at <= '{end_date}'
            AND b.status = '{bucket_status}'
            AND b.name = '{bucket_type_condition}'
            AND pr.repo_id in ({repo_ids})
            AND pr.iteration = 1
        ORDER by
            prc.scm_comment_id
        LIMIT {limit} OFFSET {offset}
    """

    code_review_time_query = """
        SELECT
            AVG(EXTRACT(EPOCH FROM (scm_close_time - scm_creation_time)) / 3600) AS avg_code_review_time_in_hours
        FROM
            pull_requests
        WHERE
            scm_creation_time IS NOT NULL
            AND scm_close_time IS NOT NULL
            AND repo_id in ({repo_ids})
            AND created_at >= '{start_date}'
            AND created_at <= '{end_date}'
            AND iteration = 1
    """

    number_of_prs_merged_query = """
        SELECT
            COUNT(*) AS num_merged_prs
        FROM
            pull_requests
        WHERE
            pr_state = 'MERGED'
            AND repo_id in ({repo_ids})
            AND created_at >= '{start_date}'
            AND created_at <= '{end_date}'
            AND iteration = 1
    """

    number_of_prs_raised_query = """
        SELECT
            COUNT(*) AS num_raised_prs
        FROM
            pull_requests
        WHERE
            repo_id in ({repo_ids})
            AND created_at >= '{start_date}'
            AND created_at <= '{end_date}'
            AND iteration = 1
    """
