from utilities import TagGit
from common.aws.codepipeline import PipelineTokens
from aws_lambda_powertools import Logger


logger = Logger()


@logger.inject_lambda_context(clear_state=True, log_event=True)
def lambda_handler(event: dict, context: dict):
    """
    Used within the CodePipeline, checks for the commit sha that is passed into the
    parameters for this lambda from the Source, and moves the tag to that commit
    """
    pipeline_values = PipelineTokens(event)

    commit_sha = pipeline_values.input_parameters.get("COMMIT_SHA")
    logger.append_keys(commitSha=commit_sha)

    client = TagGit(commit_sha)

    if client.tag_commit() is True:
        logger.info("Tag updated")
        pipeline_values.put_job_success(
            {"tagName": client.tag_name, "currentCommitSha": commit_sha}
        )

    pipeline_values.put_job_failure("Tag failed to update")
    return None
