import os
import pytest
from all_tests.pytest_utilities.general_utilities import safe_env_cleanup_list


@pytest.fixture(scope="function")
def create_env(environment: dict):
    """
    Pytest Fixture to create environment variables for tests.
    """
    os.environ = {**os.environ, **environment}

    yield

    safe_env_cleanup_list(environment.keys())
