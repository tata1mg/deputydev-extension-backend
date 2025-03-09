from packaging import version


def compare_version(str_version_1: str, str_version_2: str, comparison_operator: str) -> bool:
    """
    Compare two versions
    :param str_version_1: First version
    :param str_version_2: Second version
    :param comparision_operator: Comparision operator
    :return: True if the comparision is true, else False
    """
    version_1 = version.parse(str_version_1)
    version_2 = version.parse(str_version_2)
    operators = {
        "==": version_1 == version_2,
        ">": version_1 > version_2,
        ">=": version_1 >= version_2,
        "<": version_1 < version_2,
        "<=": version_1 <= version_2,
        "!=": version_1 != version_2,
    }
    return operators[comparison_operator]
