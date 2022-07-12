import aws_cdk as cdk
from aws_cdk import aws_logs as logs
from cdk_configs.product_properties.pipeline_and_deployment_props import (
    DeploymentFileLocation,
    ContextTag,
    DeploymentTag,
)
from cdk_configs.resource_names import DeploymentResourceName
from cdk_configs.resource_configurations.constructs import (
    CodebuildConfigs,
    LogGroupConfigs,
    TestingCodebuildEnvVariables,
    DeploymentCodebuildEnvVariables,
)
from cdk_configs.resource_configurations.common_configs import (
    PipelineCodebuildConfigs,
    NoCommonConfigs,
)


PIPELINE_CODEBUILDS = {
    DeploymentResourceName.UNIT_TESTS: CodebuildConfigs(
        common=PipelineCodebuildConfigs,
        project_name=DeploymentResourceName.UNIT_TESTS,
        description="Runs Unit Tests.",
        build_spec=DeploymentFileLocation.TESTING_BUILDSPEC,
        environment_variables=TestingCodebuildEnvVariables(
            SCRIPT="pytest all_tests/unit_tests",
            TESTING_TYPE="UnitTesting",
            SECRET_LOCATION=None,
        ),
    ),
    DeploymentResourceName.INTEGRATION_TESTS: CodebuildConfigs(
        common=PipelineCodebuildConfigs,
        project_name=DeploymentResourceName.INTEGRATION_TESTS,
        description="Runs integration tests, including active api testing for health/response checks",
        build_spec=DeploymentFileLocation.TESTING_BUILDSPEC,
        environment_variables=TestingCodebuildEnvVariables(
            SCRIPT="pytest all_tests/integration_tests",
            TESTING_TYPE="IntegrationTests",
            SECRET_LOCATION="api-credentials",
        ),
    ),
    DeploymentResourceName.CONTRACT_TESTS: CodebuildConfigs(
        common=PipelineCodebuildConfigs,
        project_name=DeploymentResourceName.CONTRACT_TESTS,
        description="Runs other teams that depend on our API's Contract Tests to ensure compatibility",
        build_spec=DeploymentFileLocation.TESTING_BUILDSPEC,
        environment_variables=TestingCodebuildEnvVariables(
            SCRIPT="pytest all_tests/external_product_tests",
            TESTING_TYPE="ContractTests",
            SECRET_LOCATION=None,
        ),
    ),
    DeploymentResourceName.DEPLOY_APP: CodebuildConfigs(
        common=PipelineCodebuildConfigs,
        project_name=DeploymentResourceName.DEPLOY_APP,
        description="Deploys the primary app",
        build_spec=DeploymentFileLocation.DEPLOY_BUILDSPEC,
        environment_variables=DeploymentCodebuildEnvVariables(
            PROD_ASSUME_ROLE="",  # Set in CDK
            CDK_ACTION="deploy",
            STACK_TO_DEPLOY=DeploymentResourceName.MAIN_STACK,
            DEPLOYMENT_TAG=f"-c {ContextTag.deploy_tag}={DeploymentTag.DEV}",
            USE_PROD_VALUES="",  # Set in CDK
        ),
    ),
    DeploymentResourceName.DEPLOY_ADHOC: CodebuildConfigs(
        common=PipelineCodebuildConfigs,
        project_name=DeploymentResourceName.DEPLOY_ADHOC,
        description="Deploys an immutable adhoc testing environment and outputs the necessary values for testing",
        build_spec=DeploymentFileLocation.DEPLOY_BUILDSPEC,
        environment_variables=DeploymentCodebuildEnvVariables(
            PROD_ASSUME_ROLE=None,
            CDK_ACTION="deploy",
            STACK_TO_DEPLOY=DeploymentResourceName.MAIN_STACK,
            DEPLOYMENT_TAG=f"-c {ContextTag.deploy_tag}={DeploymentTag.TEST}",
            USE_PROD_VALUES=None,
        ),
    ),
    DeploymentResourceName.DESTROY_ADHOC: CodebuildConfigs(
        common=PipelineCodebuildConfigs,
        project_name=DeploymentResourceName.DESTROY_ADHOC,
        description="Destroys adhoc testing environment",
        build_spec=DeploymentFileLocation.DEPLOY_BUILDSPEC,
        environment_variables=DeploymentCodebuildEnvVariables(
            PROD_ASSUME_ROLE=None,
            CDK_ACTION="destroy",
            STACK_TO_DEPLOY=DeploymentResourceName.MAIN_STACK,
            DEPLOYMENT_TAG=f"-c {ContextTag.deploy_tag}={DeploymentTag.TEST}",
            USE_PROD_VALUES=None,
        ),
    ),
}


PIPELINE_CODEBUILD_LOG_GROUP = LogGroupConfigs(
    common=NoCommonConfigs, removal_policy=cdk.RemovalPolicy.DESTROY
)
