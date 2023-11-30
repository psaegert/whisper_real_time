import os


def get_transcriptions_dir(*args: str) -> str:
    """
    Get the path to the data directory.

    Parameters
    ----------
    args : str
        The path to the data directory.

    Returns
    -------
    str
        The path to the data directory.s
    """
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', '..', 'transcriptions', *args), exist_ok=True)

    return os.path.join(os.path.dirname(__file__), '..', '..', 'transcriptions', *args)
