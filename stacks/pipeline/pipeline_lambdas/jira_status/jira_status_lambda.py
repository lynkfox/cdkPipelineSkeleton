from common.aws.codepipeline import PipelineTokens
from utilities import GitCommitHistory
from aws_lambda_powertools import Logger

logger = Logger()


@logger.inject_lambda_context(clear_state=True, log_event=True)
def lambda_handler(event: dict, context: dict) -> dict:
    """
    Used in the Pipeline, checks for the current commit of the prod tag reference
    (done before it is updated to the current commit) and does a git log to get all the
    commits between the last tag and now.

    Then parses those for Card Numbers and attempts to update each status to Done.
    """

    try:

        pipeline_values = PipelineTokens(event)

        client = GitCommitHistory(pipeline_values.input_parameters.get("COMMIT_SHA"))

        pipeline_values.put_job_success(output_variables=client.update_jira())

    except Exception as e:
        logger.exception("Error in updating jira cards")
        pipeline_values.put_job_failure("Unable to complete update values", e)

    return {}
