from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentFileLocation:
    PIPELINE_LAYER = "pipeline_lambdas/pipeline_layer.zip"
    COMMON_LAYER = "common_layer.zip"
    TESTING_BUILDSPEC = "stacks/pipeline/build_specs/buildspec_testing.yml"
    DEPLOY_BUILDSPEC = "stacks/pipeline/build_specs/buildspec_deploy_app.yml"
    ASSUME_CROSS_ACCOUNT_ROLE = "cdk_configs/bash_scripts/assume_cicd.sh"


@dataclass(frozen=True)
class ContextTag:
    deploy_tag = "deploy_tag"
    is_prod = "use_prod"


@dataclass(frozen=True)
class DeploymentTag:
    """
    environment prefix tag. It is NOT recommended that you add more, as persistent
    environments are discouraged. Anything other than prod should be ephemeral and able
    to be deleted and rebuilt on a moments notice.

    """

    DEV = "DEV"
    PROD = "PROD"
    TEST = "TEST"
    LOCAL = "LOCAL"


@dataclass(frozen=True)
class DeploymentSecretKey:
    """
    names of the keys inside the ProductSetting.DEPLOYMENT_SECRET secret

    These key names are used in the DeploymentProperties.secret() method and passed into
    that method. That method will look in the ProductSetting.DEPLOYMENT_SECRET secret in
    SecretManager for these keys to retrieve the values and use them in various stages
    of the pipeline.

    As such, if you change the location of said secrets you need to update that value.
    """

    GITHUB_TOKEN = "github-token"
    GITHUB_SERVICE_USER = "github-service-account"
    GITHUB_SERVICE_PASSWORD = "github-service-password"
    JIRA_TOKEN = "jira-token"
    JIRA_SERVICE_USER = "jira-service-account"
    JIRA_SERVICE_PASSWORD = "jira-service-password"
    PROD_ACCOUNT_NUMBER = "prod-account-number"
    CROSS_ACCOUNT_ROLE = "cross-account-role"
    DEV_DEFAULT_VPC = "dev-default-vpc-id"
    PROD_DEFAULT_VPC = "prod-default-vpc-id"
    HOST_ZONE_ID = "host-zone-id"
    HOST_ZONE_NAME = "host-zone-name"
    DOMAIN_CERT = "domain-certificate"
