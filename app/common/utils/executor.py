import concurrent.futures

from app.common.utils.config_manager import ConfigManager

max_workers = ConfigManager.configs.get("EXECUTOR_MAX_WORKERS", 1)

process_executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
