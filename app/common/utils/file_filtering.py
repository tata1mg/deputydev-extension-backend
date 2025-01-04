import os


def files_to_exclude(exclusions, inclusions, repo_dir=""):
    """
    Computes the final list of excluded files or folders after applying inclusions and exclusions.

    :param repo_dir: The root directory path for the repository.
    :param exclusions: List of paths (relative to repo_dir) to be excluded.
    :param inclusions: List of paths (relative to repo_dir) to be included even if they are within exclusions.
    :return: A set of paths (relative to repo_dir) that are effectively excluded.
    """
    exclusions = {os.path.join(repo_dir, path) for path in exclusions}
    inclusions = {os.path.join(repo_dir, path) for path in inclusions}

    final_exclusions = set()

    def is_path_excluded(path, exclusions, inclusions):
        """
        Determines if a path should be excluded based on exclusions and inclusions.
        """
        for exclusion in exclusions:
            if os.path.commonpath([path, exclusion]) == exclusion:
                for inclusion in inclusions:
                    if os.path.commonpath([path, inclusion]) == inclusion:
                        return False
                return True
        return False

    # Process exclusions, filtering out overridden paths
    for exclusion in exclusions:
        if not any(os.path.commonpath([exclusion, inclusion]) == inclusion for inclusion in inclusions):
            final_exclusions.add(exclusion)

    # Add nested files and folders to the final exclusions
    for exclusion in exclusions:
        for root, dirs, files in os.walk(exclusion):
            for item in dirs + files:
                full_path = os.path.join(root, item)
                if is_path_excluded(full_path, exclusions, inclusions):
                    final_exclusions.add(full_path)

    # Convert final exclusions to relative paths
    relative_exclusions = {os.path.relpath(path, repo_dir) for path in final_exclusions}

    return relative_exclusions
