import json
import os
from dataclasses import dataclass, field

import boto3
from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from common.aws.aws_lambda import LambdaVariables

logger = Logger(child=True)


@dataclass
class PipelineTokens(LambdaVariables):
    """
    Class for handling the incoming event to a AWS Lambda that is part of a CodePipeline.
    """

    job_id: str = field(init=False)
    input_parameters: dict = field(default=None, init=False)
    input_artifacts: list = field(default=None, init=False)
    input_credentials: dict = field(default=None, init=False)
    output_artifacts: list = field(default=None, init=False)
    client: boto3.Session.client = field(default=None, init=False)

    def __post_init__(self):
        codepipeline_job_info = self.event["CodePipeline.job"]
        self.job_id = codepipeline_job_info["id"]
        self.input_parameters = json.loads(
            codepipeline_job_info["data"]["actionConfiguration"]["configuration"].get(
                "UserParameters", '{"None": "None"}'
            )
        )
        self.input_artifacts = codepipeline_job_info["data"].get("inputArtifacts")
        self.input_credentials = codepipeline_job_info["data"].get(
            "artifactCredentials"
        )
        self.output_artifacts = codepipeline_job_info["data"].get("outputArtifacts")
        self.client = boto3.client("codepipeline")

        values_to_log = {**self.input_parameters, **{"job_id": self.job_id}}
        logger.append_keys(**values_to_log)

    def put_job_success(self, output_variables: dict) -> dict:
        """
        sends the Job Success token back to the pipeline that spawned this process
        """

        logger.info("Success", extra=output_variables)
        return self.client.put_job_success_result(
            jobId=self.job_id, outputVariables=output_variables
        )

    def put_job_failure(self, message: str, e: Exception = None) -> dict:
        """
        sends the Job Failure token back to the pipeline that spawned this process
        """
        if e is not None:
            logger.exception(message)
        else:
            logger.error(message)
        return self.client.put_job_failure_result(
            jobId=self.job_id, failureDetails={"type": "JobFailed", "message": message}
        )


def get_cross_account_client(service: str = "s3", type: str = "client", role_arn=None):
    """
    Use to retrieve a cross account client for a given service.

    Parameters:
        service: [str] - The service to retrieve - same nomenclature as Boto3 (i.e. 's3'
            or 'dynamodb').
        type: [str] -  "client" or "resource" if it can't determine it defaults to client.
        role_arn: [str] - The arn of the cross account role.

    Returns:
        Union[boto3.client, boto3.resource] session.
    """
    logger.debug("Attempting to assume cross account role")
    sts_connection = boto3.client("sts")

    try:
        acct_b = sts_connection.assume_role(
            RoleArn=os.getenv("CROSS_ACCT_ROLE_ARN", role_arn),
            # account number and role of the target dynamodb acct.
            RoleSessionName="ER-Pipeline-Cross_account-Deploy",
        )
    except ClientError as e:
        logger.warning("Unable to make Cross Account connection", exc_info=True)

        return None

    ACCESS_KEY = acct_b["Credentials"]["AccessKeyId"]
    SECRET_KEY = acct_b["Credentials"]["SecretAccessKey"]
    SESSION_TOKEN = acct_b["Credentials"]["SessionToken"]

    if type != "client":
        return boto3.resource(
            service,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            aws_session_token=SESSION_TOKEN,
        )
    else:
        return boto3.client(
            service,
            aws_access_key_id=ACCESS_KEY,
            aws_secret_access_key=SECRET_KEY,
            aws_session_token=SESSION_TOKEN,
        )
