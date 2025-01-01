import asyncio
import os
from concurrent.futures import ProcessPoolExecutor
from typing import List, Mapping, Optional, Tuple

from weaviate import WeaviateAsyncClient

from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.chunking.document import Document, chunks_to_docs
from app.common.services.chunking.vector_store.main import ChunkVectorScoreManager
from app.common.services.embedding.base_embedding_manager import BaseEmbeddingManager
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo

from .chunk import chunk_source


def read_file(file_name: str) -> str:
    """
    Reads the content of a file.

    Args:
        file_name (str): The path to the file to be read.

    Returns:
        str: The content of the file.

    Raises:
        SystemExit: If the file cannot be read due to a SystemExit exception.
    """
    try:
        with open(file_name, "r") as f:
            return f.read()
    except SystemExit:
        raise SystemExit
    except Exception:
        return ""


def create_chunks(
    file_path: str, root_dir: str, file_hash: Optional[str] = None, use_new_chunking: bool = False
) -> list[ChunkInfo]:
    """
    Converts the content of a file into chunks of code.

    Args:
        source (str): The path to the file to be processed.
        use_new_chunking(bool): to enabled new chunking strategy

    Returns:
        list[str]: A list of code chunks extracted from the file.
    """
    file_contents = read_file(os.path.join(root_dir, file_path))
    chunks = chunk_source(
        file_contents, path=file_path, file_hash=file_hash, nl_desc=False, use_new_chunking=use_new_chunking
    )
    return chunks


async def add_chunk_embeddings(chunks: List[ChunkInfo], embedding_manager: BaseEmbeddingManager) -> None:
    """
    Adds embeddings to the chunks.

    Args:
        chunks (List[ChunkInfo]): A list of chunks to which embeddings should be added.

    Returns:
        List[ChunkInfo]: A list of chunks with embeddings added.
    """
    texts_to_embed = [chunk.get_chunk_content_with_meta_data(add_ellipsis=False, add_lines=False) for chunk in chunks]
    embeddings, _input_tokens = await embedding_manager.embed_text_array(texts=texts_to_embed)
    for chunk, embedding in zip(chunks, embeddings):
        chunk.embedding = embedding


async def create_chunks_from_files(
    file_paths_and_hashes: Mapping[str, Optional[str]],
    root_dir: str,
    use_new_chunking: bool = False,
    process_executor: Optional[ProcessPoolExecutor] = None,
) -> List[ChunkInfo]:
    """
    Converts the content of a list of files into chunks of code.

    Args:
        file_path (List[str]): A list of file paths to be processed.

    Returns:
        List[ChunkInfo]: A list of code chunks extracted from the files.
    """
    chunks: List[ChunkInfo] = []

    loop = asyncio.get_event_loop()
    for file, file_hash in file_paths_and_hashes.items():
        chunks_from_file: List[ChunkInfo] = []
        if process_executor is None:
            chunks_from_file = create_chunks(file, root_dir, file_hash, use_new_chunking)
        else:
            chunks_from_file = await loop.run_in_executor(
                process_executor, create_chunks, file, root_dir, file_hash, use_new_chunking
            )
        chunks.extend(chunks_from_file)
    return chunks


async def create_chunks_without_vector_db(
    local_repo: BaseLocalRepo, use_new_chunking: bool = True, process_executor: Optional[ProcessPoolExecutor] = None
) -> List[ChunkInfo]:
    """
    Converts the content of a list of files into chunks of code.

    Args:
        file_path (List[str]): A list of file paths to be processed.

    Returns:
        List[ChunkInfo]: A list of code chunks extracted from the files.
    """
    file_list = await local_repo.get_chunkable_files()
    all_chunks: List[ChunkInfo] = await create_chunks_from_files(
        {file: None for file in file_list}, local_repo.repo_path, use_new_chunking, process_executor=process_executor
    )
    return all_chunks


async def create_chunks_with_vector_db(
    local_repo: BaseLocalRepo,
    weaviate_client: WeaviateAsyncClient,
    embedding_manager: BaseEmbeddingManager,
    use_new_chunking: bool = True,
    process_executor: Optional[ProcessPoolExecutor] = None,
    return_chunks: bool = False,
    max_batch_size_chunking: int = 100,
) -> List[ChunkInfo]:
    """
    Converts the content of a list of files into chunks of code.

    Args:
        file_path (List[str]): A list of file paths to be processed.

    Returns:
        List[ChunkInfo]: A list of code chunks extracted from the files.
    """
    file_path_commit_hash_map = await local_repo.get_chunkable_files_and_commit_hashes()
    vector_store_files = await ChunkVectorScoreManager(
        weaviate_client=weaviate_client, local_repo=local_repo
    ).get_stored_chunk_files_with_chunk_content(file_path_commit_hash_map)
    existing_files = {vector_file[0].file_path for vector_file in vector_store_files}

    files_to_chunk = {
        file: file_hash for file, file_hash in file_path_commit_hash_map.items() if file not in existing_files
    }
    files_to_chunk_items = list(files_to_chunk.items())
    final_chunks: List[ChunkInfo] = []
    for i in range(0, len(files_to_chunk), max_batch_size_chunking):
        # create batch chunks
        batch_files = files_to_chunk_items[i : i + max_batch_size_chunking]
        batched_chunks: List[ChunkInfo] = await create_chunks_from_files(
            dict(batch_files), local_repo.repo_path, use_new_chunking, process_executor=process_executor
        )
        if batched_chunks:
            await add_chunk_embeddings(batched_chunks, embedding_manager)
            await ChunkVectorScoreManager(
                local_repo=local_repo, weaviate_client=weaviate_client
            ).add_differential_chunks_to_store(batched_chunks)
            # store chunks only if we need to return
            if return_chunks:
                final_chunks.extend(
                    [
                        ChunkInfo(
                            content=vector_store_file[1].text,
                            source_details=ChunkSourceDetails(
                                file_path=vector_store_file[0].file_path,
                                file_hash=vector_store_file[0].file_hash,
                                start_line=vector_store_file[0].start_line,
                                end_line=vector_store_file[0].end_line,
                            ),
                        )
                        for vector_store_file in vector_store_files
                    ]
                )
    return final_chunks


async def source_to_chunks(
    local_repo: BaseLocalRepo,
    use_new_chunking: bool = True,
    use_vector_store: bool = True,
    weaviate_client: Optional[WeaviateAsyncClient] = None,
    embedding_manager: Optional[BaseEmbeddingManager] = None,
    process_executor: Optional[ProcessPoolExecutor] = None,
) -> Tuple[List[ChunkInfo], List[Document]]:
    """
    Converts code files within a directory into chunks of code.

    Args:
        directory (str): The path to the directory containing code files.
        config (ChunkConfig, optional): Configuration for chunking. Defaults to None.
        use_new_chunking:bool = to enable new chunking

    Returns:
        tuple[list[ChunkInfo], list[Document]]: A tuple containing a list of chunk information and a list of docs.
    """
    all_chunks, all_docs = [], []
    if use_vector_store:
        if not weaviate_client:
            raise ValueError("Weaviate client is required for vector store")
        if not embedding_manager:
            raise ValueError("Embedding manager is required for vector store")
        all_chunks = await create_chunks_with_vector_db(
            local_repo, weaviate_client, embedding_manager, use_new_chunking, process_executor=process_executor
        )
    else:
        all_chunks = await create_chunks_without_vector_db(
            local_repo, use_new_chunking, process_executor=process_executor
        )
        # Convert chunks to Document objects
        all_docs: List[Document] = chunks_to_docs(all_chunks)
    # Return both the list of chunk information and the list of file paths
    return all_chunks, all_docs


def render_snippet_array(chunks: List[ChunkInfo]) -> str:
    joined_chunks = "\n".join([chunk.get_xml() for chunk in chunks])

    start_chunk_tag = "<relevant_chunks_in_repo>"
    end_chunk_tag = "</relevant_chunks_in_repo>"
    if joined_chunks.strip() == "":
        return ""
    return start_chunk_tag + "\n" + joined_chunks + "\n" + end_chunk_tag
