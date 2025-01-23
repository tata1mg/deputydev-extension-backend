import asyncio
import copy
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.common.models.dto.chunk_dto import ChunkDTO, ChunkDTOWithVector
from app.common.models.dto.chunk_file_dto import ChunkFileDTO
from app.common.services.chunking.chunk_info import ChunkInfo, ChunkSourceDetails
from app.common.services.chunking.vector_store.dataclasses.refresh_config import (
    RefreshConfig,
)
from app.common.services.repo.local_repo.base_local_repo import BaseLocalRepo
from app.common.services.repository.chunk.chunk_service import ChunkService
from app.common.services.repository.chunk_files.chunk_files_service import (
    ChunkFilesService,
)
from app.common.services.repository.dataclasses.main import WeaviateSyncAndAsyncClients
from app.common.utils.app_logger import AppLogger


class ChunkVectorStoreManager:
    def __init__(self, local_repo: BaseLocalRepo, weaviate_client: WeaviateSyncAndAsyncClients):
        self.local_repo = local_repo
        self.weaviate_client = weaviate_client

    async def add_differential_chunks_to_store(
        self,
        file_wise_chunks: Dict[str, List[ChunkInfo]],
        custom_create_timestamp: Optional[datetime] = None,
        custom_update_timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add differential chunks to the vector store.
        :param file_wise_chunks: Dict[str, List[ChunkInfo]]
        :return: None
        """
        all_chunks_to_store: List[ChunkDTOWithVector] = []
        all_chunk_files_to_store: List[ChunkFileDTO] = []

        for chunks in file_wise_chunks.values():
            for chunk in chunks:
                if chunk.embedding is None or not chunk.source_details.file_hash:
                    raise ValueError(f"Chunk {chunk.content_hash} does not have an embedding")

                now_time = datetime.now().replace(tzinfo=timezone.utc)
                all_chunks_to_store.append(
                    ChunkDTOWithVector(
                        dto=ChunkDTO(
                            chunk_hash=chunk.content_hash,
                            text=chunk.content,
                            created_at=custom_create_timestamp if custom_create_timestamp else now_time,
                            updated_at=custom_update_timestamp if custom_update_timestamp else now_time,
                        ),
                        vector=chunk.embedding,
                    ),
                )
                all_chunk_files_to_store.append(
                    ChunkFileDTO(
                        file_path=chunk.source_details.file_path,
                        chunk_hash=chunk.content_hash,
                        file_hash=chunk.source_details.file_hash,
                        start_line=chunk.source_details.start_line,
                        end_line=chunk.source_details.end_line,
                        created_at=custom_create_timestamp if custom_create_timestamp else now_time,
                        updated_at=custom_update_timestamp if custom_update_timestamp else now_time,
                        total_chunks=len(chunks),
                    )
                )

        time_start = time.perf_counter()
        await asyncio.gather(
            ChunkService(weaviate_client=self.weaviate_client).bulk_insert(all_chunks_to_store),
            ChunkFilesService(weaviate_client=self.weaviate_client).bulk_insert(
                all_chunk_files_to_store,
            ),
        )
        time_end = time.perf_counter()
        AppLogger.log_debug(f"Inserting {len(all_chunks_to_store)} chunks took {time_end - time_start} seconds")

    async def _get_file_wise_stored_chunk_files_chunks_and_vectors(
        self,
        file_path_commit_hash_map: Dict[str, str],
    ) -> Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]:
        """
        Get the stored chunk files, chunks, and vectors based on the file path and commit hash map.
        :param file_path_commit_hash_map: Dict[str, str]
        :return: Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]
        """
        chunk_files_in_db = await ChunkFilesService(
            weaviate_client=self.weaviate_client
        ).get_chunk_files_by_commit_hashes(file_to_commit_hashes=file_path_commit_hash_map)

        if not chunk_files_in_db:
            return {}

        stored_chunks_and_vectors = await ChunkService(weaviate_client=self.weaviate_client).get_chunks_by_chunk_hashes(
            chunk_hashes=list({chunk_file.chunk_hash for chunk_file in chunk_files_in_db}),
        )

        stored_chunks_and_vectors_chunk_dict = {
            chunk_and_vector[0].chunk_hash: chunk_and_vector for chunk_and_vector in stored_chunks_and_vectors
        }

        file_wise_stored_chunk_files_and_chunks: Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]] = {}
        for chunk_file in chunk_files_in_db:
            if chunk_file.chunk_hash in stored_chunks_and_vectors_chunk_dict:
                file_wise_stored_chunk_files_and_chunks.setdefault(chunk_file.file_path, []).append(
                    (
                        chunk_file,
                        stored_chunks_and_vectors_chunk_dict[chunk_file.chunk_hash][0],
                        stored_chunks_and_vectors_chunk_dict[chunk_file.chunk_hash][1],
                    )
                )

        return file_wise_stored_chunk_files_and_chunks

    def _filter_out_invalid_files(
        self, file_wise_chunk_files_chunks_and_vectors: Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]
    ) -> Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]:
        """
        Filter out invalid files from the dictionary of file wise chunk files, chunks, and vectors.
        :param file_wise_chunk_files_chunks_and_vectors: Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]
        :return: Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]
        """

        filtered_file_wise_chunk_files_chunks_and_vectors: Dict[
            str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]
        ] = {}
        for file_path, chunk_files_chunks_and_vectors in list(file_wise_chunk_files_chunks_and_vectors.items()):
            if not chunk_files_chunks_and_vectors:
                continue
            if len(chunk_files_chunks_and_vectors) != chunk_files_chunks_and_vectors[0][0].total_chunks:
                AppLogger.log_debug(f"File {file_path} has missing chunks")
                continue
            filtered_file_wise_chunk_files_chunks_and_vectors[file_path] = chunk_files_chunks_and_vectors

        return filtered_file_wise_chunk_files_chunks_and_vectors

    def _get_file_wise_chunk_info_objects_from_chunk_files_chunks_and_vectors(
        self, file_wise_chunk_files_chunks_and_vectors: Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]
    ) -> Dict[str, List[ChunkInfo]]:
        """
        Get the file wise ChunkInfo objects from the chunk files, chunks, and vectors.
        :param file_wise_chunk_files_chunks_and_vectors: Dict[str, List[Tuple[ChunkFileDTO, ChunkDTO, List[float]]]]
        :return: Dict[str, List[ChunkInfo]]
        """
        return {
            file_path: [
                ChunkInfo(
                    content=chunk_file_chunk[1].text,
                    source_details=ChunkSourceDetails(
                        file_path=chunk_file_chunk[0].file_path,
                        file_hash=chunk_file_chunk[0].file_hash,
                        start_line=chunk_file_chunk[0].start_line,
                        end_line=chunk_file_chunk[0].end_line,
                    ),
                    embedding=chunk_file_chunk[2],
                )
                for chunk_file_chunk in chunk_files_chunks_and_vectors
            ]
            for file_path, chunk_files_chunks_and_vectors in file_wise_chunk_files_chunks_and_vectors.items()
        }

    async def _refresh_chunk_files_and_chunks(
        self,
        file_wise_chunks: Dict[str, List[ChunkInfo]],
        vector_required: bool,
        chunk_refresh_config: Optional[RefreshConfig] = None,
    ) -> None:
        """
        Refresh the chunk files and chunks based on the refresh config.
        :param file_wise_chunks: Dict[str, List[ChunkInfo]]
        :param vector_required: bool
        :param chunk_refresh_config: RefreshConfig
        :return: None
        """
        if not chunk_refresh_config:
            return

        data_to_refresh = file_wise_chunks

        # if async refresh is enabled and vector is not required, then we send a copy of the data to refresh
        # so that the original data can be used for further processing
        # this is done to avoid the vector being deleted from the original data by the time refresh actually happens
        if not chunk_refresh_config.async_refresh and not vector_required:
            data_to_refresh = copy.deepcopy(file_wise_chunks)

        refresh_task = asyncio.create_task(
            self.add_differential_chunks_to_store(
                data_to_refresh,
                custom_create_timestamp=chunk_refresh_config.refresh_timestamp,
                custom_update_timestamp=chunk_refresh_config.refresh_timestamp,
            )
        )

        if chunk_refresh_config.async_refresh:
            return

        await refresh_task

    async def get_valid_file_wise_stored_chunks(
        self,
        file_path_commit_hash_map: Dict[str, str],
        with_vector: bool,
        chunk_refresh_config: Optional[RefreshConfig] = None,
    ) -> Dict[str, List[ChunkInfo]]:
        """
        Get the stored chunks based on the file path and commit hash map.
        :param file_path_commit_hash_map: Dict[str, str]
        :param chunk_refresh_config: Optional[RefreshConfig]
        :return: Dict[str, List[ChunkInfo]]
        """

        # final dict to store the chunks
        file_wise_chunks: Dict[str, List[ChunkInfo]] = {}

        # use batch size of 1000
        batch_size = 1000

        for i in range(0, len(file_path_commit_hash_map), batch_size):
            # determine the batch
            batch = list(file_path_commit_hash_map.items())[i : i + batch_size]

            # get the stored chunk files, chunks, and vectors
            file_wise_chunk_files_chunks_and_vectors = await self._get_file_wise_stored_chunk_files_chunks_and_vectors(
                dict(batch),
            )

            # filter out invalid files
            valid_file_wise_chunk_files_chunks_and_vectors = self._filter_out_invalid_files(
                file_wise_chunk_files_chunks_and_vectors
            )

            # create ChunkInfo objects from the chunk files, chunks, and vectors
            file_wise_chunk_info_objects = self._get_file_wise_chunk_info_objects_from_chunk_files_chunks_and_vectors(
                valid_file_wise_chunk_files_chunks_and_vectors
            )

            # start the refresh process if needed
            await self._refresh_chunk_files_and_chunks(file_wise_chunk_info_objects, with_vector, chunk_refresh_config)

            # remove the embeddings if not required
            if not with_vector:
                for chunks in file_wise_chunk_info_objects.values():
                    for chunk in chunks:
                        chunk.embedding = None

            # update the final dict
            file_wise_chunks.update(file_wise_chunk_info_objects)

        return file_wise_chunks
