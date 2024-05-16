import math
import asyncio
import multiprocessing
from typing import Any, Dict, List

from sanic.log import logger
from tqdm import tqdm

from app.constants.constants import (
    CONFIDENCE_SCORE,
    MAX_LINE_CHANGES,
    PR_SIZE_TOO_BIG_MESSAGE,
)
from app.managers.openai_tools.openai_assistance import (
    create_review_thread,
    create_run_id,
    poll_for_success,
)
from app.modules.chunking.chunk_parsing_utils import source_to_chunks, render_snippet_array
from app.modules.chunking.document import Document, chunks_to_docs
from app.modules.repo import RepoModule
from app.modules.search.lexical_search import LexicalSearch
from app.modules.search.vector_search import compute_vector_search_scores
from app.modules.tokenizer.tokenize import ContentTokenizer, compute_document_tokens
from app.utils import calculate_total_diff


class CodeReviewManager:
    """Manager for processing Pull Request reviews."""

    @classmethod
    async def process_pr_review(cls, data: Dict[str, Any]) -> None:
        """Process a Pull Request review asynchronously."""
        asyncio.ensure_future(cls.background_task(data))
        return

    @staticmethod
    async def background_task(data: Dict[str, Any]) -> None:
        """Background task for processing Pull Request reviews."""
        payload: Dict[str, Any] = {
            "repo_full_name": data.get("repo_name").strip(),
            "pr_id": data.get("pr_id").strip(),
            "branch_name": data.get("branch").strip(),
            "confidence_score": data.get("confidence_score", CONFIDENCE_SCORE),
            "pr_type": data.get("pr_type"),
        }
        repo = RepoModule(payload.get("repo_full_name"), payload.get("branch_name"))
        pr_detail = await repo.get_pr_details(payload.get("pr_id"))
        if payload.get("pr_type") == "test" and not pr_detail.created:
            return
        else:
            logger.info("Processing started.")
            diff = await repo.get_pr_diff(payload.get("pr_id"))
            diff_loc = calculate_total_diff(diff)
            logger.info(f"Total diff LOC is {diff_loc}")
            if diff_loc > MAX_LINE_CHANGES:
                logger.info("Diff count is {}. Unable to process this request.".format(diff_loc))
                comment = PR_SIZE_TOO_BIG_MESSAGE.format(diff_loc)
                await repo.create_comment_on_pr(payload.get("pr_id"), comment)
                return
            else:
                repo.clone_repo()
                all_chunks, _ = source_to_chunks(repo.repo_dir)
                all_docs: List[Document] = chunks_to_docs(all_chunks, len(repo.repo_dir) + 1)
                index = LexicalSearch()
                all_tokens = []
                try:
                    # use 1/4 the max number of cores
                    with multiprocessing.Pool(processes=math.ceil(multiprocessing.cpu_count() // 4)) as p:
                        for i, document_token_freq in tqdm(
                            enumerate(p.imap(compute_document_tokens, [doc.content for doc in all_docs])),
                            total=len(all_docs),
                        ):
                            all_tokens.append(document_token_freq)
                    for doc, document_token_freq in tqdm(
                        zip(all_docs, all_tokens), desc="Indexing", total=len(all_docs)
                    ):
                        index.add_document(title=doc.title, token_freq=document_token_freq)
                except FileNotFoundError as e:
                    logger.exception(e)

                for chunk in all_chunks:
                    chunk.source = chunk.source[len(repo.repo_dir) + 1 :]

                search_tokens = ContentTokenizer(diff).get_all_tokens()
                content_to_lexical_score_list = index.search_index(search_tokens)
                files_to_scores_list = await compute_vector_search_scores(diff, all_chunks)
                for chunk in tqdm(all_chunks):
                    vector_score = files_to_scores_list.get(chunk.denotation, 0.04)
                    chunk_score = 0.02
                    if chunk.denotation in content_to_lexical_score_list:
                        chunk_score = content_to_lexical_score_list[chunk.denotation] + (vector_score * 3.5)
                        content_to_lexical_score_list[chunk.denotation] = chunk_score
                    else:
                        content_to_lexical_score_list[chunk.denotation] = chunk_score * vector_score

                ranked_snippets_list = sorted(
                    all_chunks,
                    key=lambda chunk: content_to_lexical_score_list[chunk.denotation],
                    reverse=True,
                )[:10]

                relevant_chunk = render_snippet_array(ranked_snippets_list)

                print("------ relevant_chunk start")
                print(relevant_chunk)

                # Send final chunks and PR to LLM
                thread = await create_review_thread(diff, pr_detail, relevant_chunk)
                run = await create_run_id(thread)
                response = await poll_for_success(thread, run)
                if response:
                    comments = response.get("comments")
                    logger.info("PR comments: {}".format(comments))
                    if any(
                        float(comment.get("confidence_score")) >= float(payload.get("confidence_score"))
                        for comment in comments
                    ):
                        for comment in comments:
                            if float(comment.get("confidence_score")) >= float(payload.get("confidence_score")):
                                await repo.create_comment_on_pr(payload.get("pr_id"), comment)
                    else:
                        logger.info("LGTM!")
                        await repo.create_comment_on_pr(payload.get("pr_id"), "LGTM!!")
                repo.delete_repo()
                return
