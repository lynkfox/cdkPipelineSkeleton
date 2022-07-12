from cdk_configs.resource_names import ProductLambdaName, DeploymentResourceName
from cdk_configs.product_properties.common_props import ProductSetting
from cdk_configs.product_properties.pipeline_and_deployment_props import (
    DeploymentSecretKey,
)
from enum import Enum


class EnvTagSelector(Enum):
    """
    Used to select the proper environment variables and keep the listings together.

    These are NOT to be used in the product code itself to reference environment specific
    functionality, instead  use common.constants.environment.Environment.PROD or .NON_PROD
    """

    PROD = 1
    """
    Used in combination with the cdk_configs.product_properties.environment_variables.ENV_VARIABLES
    mapping will select the prod version of the environment variables
    """

    NON_PROD = 2
    """
    Used in combination with the cdk_configs.product_properties.environment_variables.ENV_VARIABLES
    mapping will select the non-prod version of the environment variables
    """

    COMMON = 3
    """
    Used in combination with the cdk_configs.product_properties.environment_variables.ENV_VARIABLES
    to select the environment agnostic environment variables
    """


class EnvironmentVariables:
    """
    Common class for Environment Variables data
    """

    def __init__(self, common: dict = {}, **kwargs) -> None:
        """
        Parameters;
            common: [dict] - A dictionary of common variables that can be combined for
                multiple environment dictionary responses.
            **kwargs: [str] - As many key word arguments as needed. Each kwarg name
                directly translates into the environment variable name.

        Example:
            EnvironmentVariables(
                MY_VARIABLE="Something"
            )
            >> { "MY_VARIABLE": "Something" }
        """

        self.variables = {**common, **kwargs}

    def as_dict(self, additional: dict = {}) -> dict:
        """
        Returns the env variables as a dictionary

        Parameters:
            additional: [Dictionary]: Optional, for adding additional properties in
            cdk. Should only be used in the LambdaConfig class
        """
        return self.variables


# NOTE:
# The LambdaConfigs class automatically sets the following Environment Variables on
# every lambda:
#
# POWERTOOLS_SERVICE_NAME: Name of the lambda
# LOG_LEVEL:  DEBUG if not DeploymentProperties.PRODUCTION_DEPLOYMENT, INFO otherwise
# ENVIRONMENT: either Prod or Non-Prod
#
#

common_variables = {"COMMON_TO_MANY_LAMBDAS": "Some Common oft used variable"}

common_pipeline_lambda = {"SECRET_NAME": ProductSetting.DEPLOYMENT_SECRETS}

ENV_VARIABLES = {
    ################################################
    # Product Lambdas
    ################################################
    #
    # Hello World Lambda
    #
    ProductLambdaName.HELLO_WORLD: {
        EnvTagSelector.COMMON: EnvironmentVariables(
            common=common_variables,
            ANY_KEY="SomeCommonValue",
            COMMON_KEY="Some Other Value",
        ),
        EnvTagSelector.PROD: EnvironmentVariables(
            ENV_VARIABLE_ONE="Prod Value 1", ENV_VARIABLE_TWO="Prod Value 2"
        ),
        EnvTagSelector.NON_PROD: EnvironmentVariables(
            ENV_VARIABLE_ONE="Non-Prod Value 1",
            ENV_VARIABLE_TWO="Non-Prod Prod Value 2",
        ),
    },
    #
    # Goodbye for Now Lambda
    #
    ProductLambdaName.GOODBYE_FOR_NOW: {EnvTagSelector.COMMON: common_variables},
    ################################################
    # Pipeline Lambdas                             #
    ################################################
    #
    # Github Tag
    #
    DeploymentResourceName.GITHUB_TAG: {
        EnvTagSelector.COMMON: EnvironmentVariables(
            common=common_pipeline_lambda,
            GIT_SECRET_KEY=DeploymentSecretKey.GITHUB_TOKEN,
            GITHUB_URL=ProductSetting.GITHUB_ENTERPRISE_URL,
            REPO_NAME=ProductSetting.GITHUB_FULL_REPO,
        ),
        EnvTagSelector.NON_PROD: EnvironmentVariables(
            BRANCH_NAME=ProductSetting.GITHUB_DEV_BRANCH, TAG="Dev"
        ),
        EnvTagSelector.PROD: EnvironmentVariables(
            BRANCH_NAME=ProductSetting.GITHUB_MAIN_BRANCH, TAG="Prod"
        ),
    },
    DeploymentResourceName.JIRA_STATUS: {
        EnvTagSelector.COMMON: EnvironmentVariables(
            common=common_pipeline_lambda,
            GIT_SECRET_KEY=DeploymentSecretKey.GITHUB_TOKEN,
            JIRA_SECRET_KEY=DeploymentSecretKey.JIRA_TOKEN,
            JIRA_SECRET_USER=DeploymentSecretKey.JIRA_SERVICE_USER,
            JIRA_URL=ProductSetting.JIRA_URL,
            JIRA_PROJECT=ProductSetting.JIRA_PROJECT,
            GITHUB_URL=ProductSetting.GITHUB_ENTERPRISE_URL,
            REPO_NAME=ProductSetting.GITHUB_FULL_REPO,
        ),
        EnvTagSelector.NON_PROD: EnvironmentVariables(
            BRANCH_NAME=ProductSetting.GITHUB_DEV_BRANCH,
            TAG="Dev",
            UPDATE_TO_STATUS="REVIEW"  # Note - this value must match a member name of
            # common.jira_integration.jira_client.JiraStatus
        ),
        EnvTagSelector.PROD: EnvironmentVariables(
            BRANCH_NAME=ProductSetting.GITHUB_MAIN_BRANCH,
            TAG="Prod",
            UPDATE_TO_STATUS="DONE",
        ),
    },
}
