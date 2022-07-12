from dataclasses import dataclass


@dataclass(frozen=True)
class Environment:
    """
    To be used as Environment feature flags for functionality that does not apply to one
    or the other, such as as specific advanced error recording or work in progress
    functionalities.

    As with all things CICD, longstanding environments are NOT BEST PRACTICE and so
    there should never be any more values added here.
    """

    PROD = "prod"
    NON_PROD = "non-prod"
