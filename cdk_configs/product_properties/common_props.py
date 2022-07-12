from __future__ import annotations
from dataclasses import dataclass, field
import os
import getpass
from typing import Any
import git  # this is GitPython
import aws_cdk.aws_ssm as ssm
import aws_cdk.aws_ec2 as ec2
import aws_cdk as cdk
from constructs import Construct
import aws_cdk.aws_secretsmanager as secretsmanager
from cdk_configs.product_properties.pipeline_and_deployment_props import (
    ContextTag,
    DeploymentTag,
    DeploymentSecretKey,
)
from cdk_configs.product_properties.product_properties import (
    CommonProductProperties,
    DevProductProperties,
    ProductionProductProperties,
)
from cdk_configs.utilities.color import as_warning
from datetime import datetime
from dateutil.tz import UTC
import boto3
import json
from uuid import uuid4


@dataclass(frozen=True)
class ProductSetting:
    """
    Update these settings depending on your particular product
    """

    PRIMARY_REGION = "us-east-1"
    FAILOVER_REGION = "us-west-1"

    JIRA_PROJECT = "SABC"
    JIRA_URL = "https://stateautoinsurance.atlassian.net/"
    GITHUB_ENTERPRISE_URL = "https://github.ent.stateauto.com"
    GITHUB_ORG = "DigitalLabs"
    GITHUB_REPO = "SA-ABCProduct"
    GITHUB_FULL_REPO = f"{GITHUB_ORG}/{GITHUB_REPO}"
    GITHUB_MAIN_BRANCH = "main"
    GITHUB_DEV_BRANCH = "dev"
    PRODUCT_TEAM = "SA ABCTeam"
    PRODUCT_TAG = "ABC"
    # API_SECRETS = "api-credentials"  # Only necessary if Integration/Contract tests are calling apis directly
    DEPLOYMENT_SECRETS = "plq-pipeline"  # "deployment"
    DEV_ACCOUNT_NAME = "MSD0099"
    PROD_ACCOUNT_NAME = "MSP0099"
    CODESTAR_CONNECTION = "*"
    _base_domain_name = "stateauto.com"
    DOMAIN_NAME_PREFIX = "abc"

    # It is highly recommended you get these values into Secrets and modify where they
    # are referenced to pull from secrets instead.
    AWS_ACCOUNT = "634687050145"
    VPC_ID = "vpc-0b6abe502062f462f"

    @classmethod
    def domain_name(cls, env: DeploymentTag) -> str:
        """
        builds the domain name
        """
        prefix = (
            cls.DEV_ACCOUNT_NAME if env is DeploymentTag.PROD else cls.PROD_ACCOUNT_NAME
        )

        return f"{cls.DOMAIN_NAME_PREFIX}.{prefix}.{cls._base_domain_name}"


@dataclass(frozen=True)
class CloudformationOutputs:
    API_ENDPOINT = "ApiEndpoint"
    DOMAIN_NAME = "DomainName"


@dataclass
class DeploymentProperties:
    """
    Common deployment properties for any stack in your product. Pass this class in as an
    argument to make use of its values within a given stack

    Parameters:
        app: [cdk.app] - pass the cdk.app in order to provide functionality throughout.
        prod_deployment: [bool] (Default: False) if set true this is a prod deployment.

    Properties:
        DEPLOYMENT_TAG: [DeploymentTag value] - a tag to prefix resources with. Note, this
            does not have any affect on the deployment account if used manually with
            `cdk deploy` - only if the pipeline kicked off by a push to the prod branch.
        USING_PRODUCTION_VALUES: [bool] - Are we pretending this env is production (or
            it is production)
        IS_TEST_ENV: [bool] - Is this an ephemeral Test Environment?
        DEPLOYMENT_DATE - Date of the time this stacks resources were last deployed
        COMPLETE_DOMAIN_NAME - The combined domain name

    Methods:
        prefix_tag_resource(resource_name:str=None, custom_prefix:str=None):
            creates a prefix based on deployment factors to add to a resource name
            for multi deployment separation.
            custom_prefix can be provided to add an additional prefix to the beginning

        vpc():
            sets up if not called yet and returns or just returns the vpc construct.

        secret(key: str):
            If no secrets are retrieved yet will retrieve them, otherwise will it will
            attempt to find the secret by the key provided.



    """

    app: Any
    aws_environment: cdk.Environment = field(init=False)
    PROD_DEPLOYMENT: bool = field(init=False)
    DEPLOYMENT_TAG: str = field(init=False)
    USING_PRODUCTION_VALUES: bool = field(init=False, default=False)
    IS_TEST_ENV: bool = field(init=False, default=False)
    DEPLOYMENT_DATE: str = field(init=False)
    COMPLETE_DOMAIN_NAME: str = field(init=False)

    _vpc: ec2.Vpc = field(init=False, default=None)
    _user: str = field(init=False, default="CDK")
    _commit_sha: str = field(init=False, default=None)
    _scope: Any = field(init=False, default=None)
    _secrets: dict = field(init=False, default=None)
    branch_name: str = field(init=False)

    def __post_init__(self):
        self.DEPLOYMENT_TAG = try_get_context(ContextTag.deploy_tag, self.app)
        self.PROD_DEPLOYMENT = try_get_context(ContextTag.is_prod, self.app)
        self.DEPLOYMENT_DATE = datetime.now(tz=UTC).isoformat()
        self._get_commit_sha()

        if not self.PROD_DEPLOYMENT and self.DEPLOYMENT_TAG is not DeploymentTag.DEV:
            self.IS_TEST_ENV = True

        if self.DEPLOYMENT_TAG is DeploymentTag.TEST or self.PROD_DEPLOYMENT:
            self.USING_PRODUCTION_VALUES = True

        self._compose_domain_name()

        self._set_environment()

        self._set_user()
        self.branch_name = (
            ProductSetting.GITHUB_MAIN_BRANCH
            if self.PROD_DEPLOYMENT and not self.IS_TEST_ENV
            else ProductSetting.GITHUB_DEV_BRANCH
        )

    def _get_commit_sha(self):
        """
        if its a test env, sets the git commit sha (the first 7 digits) for use in
        telling test environments apart.

        Note: This uses GitPython which works through the base .git folder. This means
        that it *does* work in codebuilds IF the source made a proper git clone (even
        a shallow one) as well as working in a local env.

        However, using other methods than CodeBuild of synth-ing/deploying the product
        this will not work and it would have to be passed into that stage by the
        Pipeline Variables themselves
        """
        if self.IS_TEST_ENV:
            self._commit_sha = git.Repo(
                search_parent_directories=True
            ).head.commit.hexsha[:7]

    def _compose_domain_name(self):
        """
        Gets the domain name depending on if its a Prod deployment or not, then attaches
        the commit sha if its a test env and the product tag. End result would look
        something like:

            abc.msp0099.stateauto.com
            9acd32.abc.msd0099.stateauto.com
        """
        settings = (
            ProductionProductProperties
            if self.PROD_DEPLOYMENT and not self.IS_TEST_ENV
            else DevProductProperties
        )

        values = (
            [self._commit_sha]
            if self._commit_sha is not None and self.IS_TEST_ENV
            else []
        )
        values.extend([ProductSetting.PRODUCT_TAG, settings.DOMAIN_NAME])
        self.COMPLETE_DOMAIN_NAME = ".".join(values).lower()

    def _set_environment(self):
        """
        Sets the `DeploymentProperties.aws_environment` for use in stack creation.
        """

        # Note: you'll want to update this function to be more secure and be able to
        # handle active-active failover deployment to multiple regions

        self.aws_environment = cdk.Environment(
            account=ProductSetting.AWS_ACCOUNT, region=ProductSetting.PRIMARY_REGION
        )

    def _set_user(self):
        """
        Determines user deploying stack if deployed from local. If from pipeline, will
        be set to "Pipeline"
        """
        if os.getenv("IS_PIPELINE") is None:
            self._user = getpass.getuser().upper().replace("\\", "").replace("SAI", "")
        else:
            self._user = "Pipeline"

    def vpc(self, scope: Construct):
        """
        Gets or if not yet been gotten, instantiates the VPC object. Expects there to be
        a secret in the same account as this stack is deploying in named `deployment`
        that contains a key named `vpc`

        """
        try:

            already_defined = (
                self._scope in scope.scopes if hasattr(scope, "scopes") else False
            )
        except Exception:
            already_defined = False

        # If vpc is none, then this has never been run so grab the vpc
        # however, if scope is different than the last time, then we're going to want
        # to re-look up the vpc information.
        if self._vpc is None and not already_defined:
            self._vpc = ec2.Vpc.from_lookup(
                scope,
                f"VPC-import-{uuid4()}",  # required to make sure logical ids dont overlap
                vpc_id=ProductSetting.VPC_ID,
            )
            # Note: If your Pipeline for prod uses Cross Account status, then you'll
            # want to add a conditional to the get_secrets call above in order to
            # differentiate between which secret for dev or prod, and both values will
            # need to be in the same secret key in Secret Manager
            # This part is a bit tricky as secrets and dealing with cross account actions
            # can become pretty funky.

        # log the scope so we dont instantiate a from_lookup resource multiple times
        # in the same stack
        self._scope = scope
        return self._vpc

    def prefix_tag(
        self,
        resource_name: str = None,
        custom_prefix: str = None,
    ) -> str:
        """
        Returns the prefixed tag for a resource. This is used to be able to deploy
        multiple environments without overlapping names.

        Example: "ABC-DEV-XYC1234" that can then be prefixed onto the resource name

        Parameters:
            resource_name: [str] - If not None, returns the entire prefix+name
            custom_prefix: [str] - Appends this to the front of the prefix for additional
                customization.
        """
        prefixes = [custom_prefix] if custom_prefix is not None else []
        prefixes.extend([ProductSetting.PRODUCT_TAG, self.DEPLOYMENT_TAG])

        if self.IS_TEST_ENV and self._commit_sha is not None:
            prefixes.append(self._commit_sha)

        if self.DEPLOYMENT_TAG is DeploymentTag.LOCAL and self._user is not None:
            prefixes.append(self._user)

        if resource_name is not None:
            prefixes.append(resource_name)

        return "-".join(prefixes)

    def secret(
        self, secret_key: DeploymentSecretKey, default_value: str = "NoSecretDefault"
    ) -> str:
        """
        Checks the secret defined in ProductSetting.DEPLOYMENT_SECRET in the account the
        stack is being deployed in for the key.

        Parameters:
            secret_key: [String]: The key within the secret. Use something like
                DeploymentSecretKey constant class for conformity
            default_value: [String]: Optional value if the secret is not found. Will
                print a statement to the terminal on a cdk action if the value was
                defaulted.

        Returns:
            (String): The secret string or decoded secret binary.
        """

        if self._secrets is None:
            session = boto3.session.Session()
            client = session.client(
                service_name="secretsmanager", region_name=self.aws_environment.region
            )

            secret_value_response = client.get_secret_value(
                SecretId=ProductSetting.DEPLOYMENT_SECRETS
            )

            if "SecretString" in secret_value_response:
                self._secrets = json.loads(secret_value_response["SecretString"])

        try:
            return self._secrets[secret_key]
        except KeyError as e:
            print(
                f"* WARNING: \n"
                + f"{as_warning(f'Secret Key {e.args[0]} not found in SecretManager ')}"
                + f"{ProductSetting.DEPLOYMENT_SECRETS} - setting to default"
                + "\n    This will need to be corrected for the system to work as intended."
                + "\n"
            )
            return default_value


def get_parameter_store_value(scope: Any, parameter_name: str) -> str:
    """
    wrapper for retrieving parameter store NON SECURE strings for use during CDK
    synthesis. This does not work for regular applications of the SDK/Boto3 - only
    during CDK synth and as a byproduct, deploy.
    """

    return ssm.StringParameter_for_string_parameter(scope, parameter_name)


def get_secret(scope: Any, secret_name: str, secret_key: str) -> str:
    """
    wrapper for retrieving Secret Manager managed secure strings for use during CDK
    synthesis. This does not work for regular applications of the SDK/Boto3 - only
    during CDK synth and as a byproduct, deploy.
    """

    return secretsmanager.Secret.from_secret_name_v2(scope, secret_name, secret_key)


def try_get_context(key, app):
    """
    Wrapper around app.node.try_get_context from CDK in order to use an constant value for
    default values.

    If additional context tags are desired, add the defaults here to ensure they get
    included with default context
    """

    defaults = {
        ContextTag.deploy_tag: DeploymentTag.LOCAL,
        ContextTag.is_prod: False,
        "user": None,
    }

    cdk_json_value = app.node.try_get_context(key)

    if key is ContextTag.is_prod and cdk_json_value is not None:
        return True

    return cdk_json_value if cdk_json_value is not None else defaults.get(key)
