import json
import os
from jsonpath_ng import parse
from cdk_configs.product_properties.common_props import (
    CloudformationOutputs,
    ProductSetting,
)
from cdk_configs.product_properties.pipeline_and_deployment_props import DeploymentTag


def get_adhoc_test_env_endpoint():
    """
    Relies on the fact that the AWS CodeBuild that builds the Adhoc Test Environment
    uses the cdk flag `--outputs-file cdk-outputs.json`. Because the Adhoc Codebuild
    creates an artifact of the environment after the cdk deploy command is run, and
    the subsequent Contract Test codebuild uses that as a source artifact, we can look
    and pull for contract tests the api to use from that file

    This function ONLY returns the base url. For any additional resources / paths either
    the test itself or another function will have to add them
    """

    try:
        with open("cdk-outputs.json") as file:
            stack_outputs = json.load(file)
            expression = parse(f"*.{CloudformationOutputs.API_ENDPOINT}")
            api_end_point = expression.find(stack_outputs)[0].value

    except Exception as e:
        # Useful for local running of the test - just make sure there is no
        # cdk-outputs.json file in the root and we can default to the dev environment
        # when running these tests in local.
        api_end_point = ProductSetting.domain_name(DeploymentTag.DEV)
        pass

    finally:
        return api_end_point
