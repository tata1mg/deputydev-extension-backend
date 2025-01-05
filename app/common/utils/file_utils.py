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
