import os


def safe_env_cleanup(env_variable_name: str):
    """
    Safely removes a single env variable to keep tests clean
    """
    if os.getenv(env_variable_name) is not None:
        del os.environ[env_variable_name]


def safe_env_cleanup_list(env_variable_names: list):
    """
    Safely cleans up a list of environment names to make sure further tests are not
    polluted
    """
    for name in env_variable_names:
        safe_env_cleanup(name)
