import concurrent.futures

from torpedo import CONFIG

max_wrokers = CONFIG.config.get("EXECUTOR_MAX_WORKERS", 1)

executor = concurrent.futures.ProcessPoolExecutor(max_workers=max_wrokers)
