from __future__ import annotations
from dataclasses import dataclass, field
from aws_cdk import aws_lambda
import aws_cdk as cdk
from aws_cdk import aws_logs as logs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_apigateway as apigateway
from cdk_configs.resource_configurations.common_configs import (
    CommonCDKConfigs,
    json_200_integration_response,
    json_200_method_response,
)
from typing import Union, Optional, List, Dict
from cdk_configs.product_properties.pipeline_and_deployment_props import (
    ContextTag,
    DeploymentFileLocation,
)
from cdk_configs.product_properties.product_properties import (
    ProductionProductProperties,
    DevProductProperties,
)
from cdk_configs.product_properties.environment_variables import (
    ENV_VARIABLES,
    EnvTagSelector,
    EnvironmentVariables,
)
from common.constants.environment import Environment
from pathlib import Path
import os

#######################################################################################
#                                                                                     #
#   Parent classes for common (non changing between resource) cdk properties and      #
#   dynamic (each resource is different) cdk properties. Not to be used directly      #
#   in a cdk stack, rather only their children                                        #
#                                                                                     #
#######################################################################################


@dataclass
class DynamicCDKConfigs:
    """
    children of this class are used to generate specific resource types properties that
    will change between every instantiation of the resource. Such as name or code
    location.

    Note that update_base_directory and self.base_directory may not apply to all resources.
    If it does not apply to a given child, then in the __post_init__ of said child, set
    self._base_directory_set=True to bypass this requirement.

    It exists in this parent class to prevent repeated boiler plate code that is needed
    for many different resource types that do have to have an asset location'

    If additional properties are needed to direct the configuration of a given construct,
    then prefix that property with `x_` and it will be ignored when producing the props
    output.

    Internal class variables prefixed with `_` in the tradition of python as "Private"
    will also be ignored.
    """

    common: Union[CommonCDKConfigs, dict]
    _necessary_values_set: Path = field(init=False)

    def __post_init__(self):
        try:
            if not isinstance(self.common, dict):
                self.common = self.common.props()

            if not isinstance(self.common, dict):
                raise Exception()
        except Exception:
            raise ValueError("common property must be a CDKProps child class or dict")

    def update_with_deployment_specific_values(self):
        """
        When implementing this function, make sure to set self._base_directory_set to
        True as the last step in order for props() not to raise a value error.
        """

        raise NotImplementedError(
            "Child class did not implement update_with_deployment_specific_values "
            + "method or has no need to implement it."
        )

    def props(self) -> dict:
        """
        Returns a dictionary of properties for a given Resource type. Can then be used
        in CDK resource instantiation like:
            resource = aws_cdk.SomeResource(
                scope,
                logical_id,
                **DynamicCDKConfigsChild.props()
            )
        """

        if not self._necessary_values_set:
            raise ValueError(
                "Call update_with_deployment_specific_values() "
                + "before or during calling props()"
            )

        return {
            **{
                key: value
                for key, value in self.__dict__.items()
                if value is not None
                and (not key.startswith("_") and not key.startswith("x_"))
                and key != "common"
            },
            **self.common,
        }

    def _prefix_name(self, prefix: str):
        """
        Searches for properties of the class for one that contains name and prepends the
        prefix to the name.
        """
        for key, value in self.__dict__.items():
            if not key.startswith("_") and "name" in key:
                setattr(self, key, f"{prefix}-{value}")
                break


#######################################################################################
#                                                                                     #
#   Specific Resource types dynamic properties, such as name, code locations, ect.    #
#                                                                                     #
#   Each class corresponds to a specific Resource type and will implement whatever    #
#   is necessary to generate the proper properties dictionary.                        #
#                                                                                     #
#   They should also always  call `super().__post_init__()` in their own              #
#    __post_init__                                                                    #
#                                                                                     #
#######################################################################################


##########################################
#   Lambdas                              #
##########################################
@dataclass
class LambdaFunctionConfigs(DynamicCDKConfigs):
    """
    This dataclass is used to generate the function Name, handler, and code asset
    locations for any lambda.  The intent is to use this in a mapping object so that
    the given stack implementing several lambdas can do so with a very easy to do
    loop and remain clean no matter the number of lambdas being implemented.

    Parameters:
        common: [CDKProps] (from parent) - The CDKProps child class this resource
            will use as common properties. It must be a lambda specific one.
        function_name [str]: Using one of the cdk_configs.resource_names Constant classes
        location: [str] In the nature of an import path of the directory, handler file, and
            handler:
                i.e. "this_and_that_lambda.this_lambda.lambda_handler

        x_link_to_dynamo: [bool] - Flag to tell the CDK stack to link to the dynamos provided
            n update_with_deployment_specific_values and for use in loops in CDK
        x_link_to_bucket: [bool] - Flag to tell the CDK stack to link to the buckets provided
            n update_with_deployment_specific_values and for use in loops in CDK


    NOTE: these are convenience flags if there are many lambdas to attach to the same
    dynamo/bucket.

    If there are very specific individual buckets/dynamos that have to be attached,
    another solution would have to be used, either modifying this class further or
    taking care of it directly in the CDK.




    Methods:
        props(): (from parent)
            returns a dictionary of properties to be slotted into the kwargs of a Lambda
            resource.

        update_with_deployment_specific_values(
            base_directory:Path,
            name_prefix: str,
            dynamodbs: List[aws_cdk.aws_dynamodb.Table],
            buckets: List[aws_cdk.aws_s3.Bucket] )

            configures this lambda for the particular environment it will be deployed too.
    """

    function_name: str
    location: str
    x_link_to_dynamo: bool = field(default=False)
    x_link_to_bucket: bool = field(default=False)
    handler: str = field(init=False)
    code: str = field(init=False)
    environment: Dict[str, str] = field(init=False, default_factory=dict)
    _common_name: str = field(init=False, default="")

    def __post_init__(self):
        super().__post_init__()
        self._common_name = self.function_name

    def props(
        self,
        base_directory: Path,
        name_prefix: str,
        prod_deployment: bool = False,
        dynamodbs: List[dynamodb.Table] = list(),
        buckets: List[s3.Bucket] = list(),
    ) -> dict:
        """
        Parameters:
            base_directory: [Path] - A Path or Path Like object for the location of the
            lambda directory
            name_prefix: [str] - The resource name prefixed with the deployment values.
            prod_deployment: [bool] - If this is a prod deployment (and so retaining
                data). Safest way to set is to use DeploymentProperties.PROD_DEPLOYMENT
            dynamodbs: List[aws_cdk.aws_dynamodb.Table] - a list of all Tables to attach
                to this Lambda's environment variables.
            buckets: List[aws_cdk.aws_s3.Bucket] - a list of all Buckets to attach to
                this Lambda's environment variables


        Raises:
            ValueError if location is not in the format of directory.file.handler
            ValueError if x_link_to_dynamo is True but no tables passed
            ValueError if x_link_to_bucket is True but no buckets passed
        """
        self.update_with_deployment_specific_values(
            base_directory, name_prefix, prod_deployment, dynamodbs, buckets
        )
        return super().props()

    def update_with_deployment_specific_values(
        self,
        base_directory: Path,
        name_prefix: str,
        prod_deployment: bool = False,
        dynamodbs: List[dynamodb.Table] = list(),
        buckets: List[s3.Bucket] = list(),
    ):
        """
        Parameters:
            base_directory: [Path] - A Path or Path Like object for the location of the
            lambda directory
            name_prefix: [str] - The resource name prefixed with the deployment values.
            prod_deployment: [bool] - If this is a prod deployment (and so retaining
                data). Safest way to set is to use DeploymentProperties.PROD_DEPLOYMENT
            dynamodbs: List[aws_cdk.aws_dynamodb.Table] - a list of all Tables to attach
                to this Lambda's environment variables.
            buckets: List[aws_cdk.aws_s3.Bucket] - a list of all Buckets to attach to
                this Lambda's environment variables


        Raises:
            ValueError if location is not in the format of directory.file.handler
            ValueError if x_link_to_dynamo is True but no tables passed
            ValueError if x_link_to_bucket is True but no buckets passed
        """
        self._build_environment_variables(
            name_prefix, dynamodbs, buckets, prod_deployment
        )

        self._prefix_name(name_prefix)

        location_parts = self.location.split(".")
        if len(location_parts) == 0:
            raise ValueError(
                f"Unable to parse location of lambda {self.function_name}. "
                + "Please validate location format (directory.file.handler)"
            )

        # set the two kwarg arguments needed for aws_cdk.aws_lambda to find the code
        self.handler = ".".join(location_parts[1:])
        self.code = aws_lambda.AssetCode(
            os.path.join(base_directory, location_parts[0])
        )

        # clean up these to None so the .props() parent method does not output them
        self.location = None
        self._necessary_values_set = True

    def _build_environment_variables(
        self,
        name_prefix: str,
        dynamodbs: List[dynamodb.Table],
        buckets: List[s3.Bucket],
        prod_deployment: bool,
    ) -> None:
        """
        Builds the environment variable dictionary, including attached dynamo and buckets

        Raises:
            ValueError if x_link_to_dynamo is True but no tables passed
            ValueError if x_link_to_bucket is True but no buckets passed
        """
        every_lambda_env = {
            "POWERTOOLS_SERVICE_NAME": self._common_name,
            "LOG_LEVEL": "INFO" if prod_deployment else "DEBUG",
            "ENVIRONMENT": Environment.PROD
            if prod_deployment
            else Environment.NON_PROD,
        }

        common_env = ENV_VARIABLES.get(self._common_name, {}).get(
            EnvTagSelector.COMMON, {}
        )

        common_env = (
            common_env.as_dict() if not isinstance(common_env, dict) else common_env
        )

        deployment_specific_env = ENV_VARIABLES.get(self._common_name, {}).get(
            EnvTagSelector.PROD if prod_deployment else EnvTagSelector.NON_PROD, {}
        )

        self.environment = (
            deployment_specific_env.as_dict(
                additional={**every_lambda_env, **common_env}
            )
            if not isinstance(deployment_specific_env, dict)
            else {**deployment_specific_env, **common_env, **every_lambda_env}
        )

        self._attach_dynamodbs(dynamodbs, name_prefix)
        self._attach_buckets(buckets, name_prefix)

    def _attach_dynamodbs(
        self, constructs: List[dynamodb.Table], name_prefix: str
    ) -> None:
        """
        Adds the table name to the environment variables, under the name of the table
        without the prefix

        Raises Value Error if config x_link_to_dynamo is TRUE but no tables passed
        """

        if self.x_link_to_dynamo and (constructs is None or len(constructs) == 0):
            raise ValueError(
                f"{self.function_name} is set to include Dynamos, but none were passed"
            )

        if self.x_link_to_dynamo:
            for table in constructs:
                # Construct objects in CDK do not have their names assigned until
                # deployment. They would just be a token. However, since we use the
                # same Name.Name to form the *logical id* of a given construct definition
                # we can tap into that here with .node.id to retrieve that same value.
                self.environment[
                    table.node.id.replace(name_prefix, "").replace("-", "_").upper()
                ] = table.table_name

    def _attach_buckets(self, constructs: List[s3.Bucket], name_prefix: str) -> None:
        """
        Adds the bucket name to the environment variables, under the name of the bucket
        without the prefix

        Raises Value Error if config x_link_to_bucket is TRUE but no buckets passed
        """

        if self.x_link_to_bucket and (constructs is None or len(constructs) == 0):
            raise ValueError(
                f"{self.function_name} is set to include Buckets, but none were passed"
            )

        if self.x_link_to_bucket:
            conformed_prefix = name_prefix.lower()
            # Construct objects in CDK do not have their names assigned until
            # deployment. They would just be a token. However, since we use the
            # same Name.Name to form the *logical id* of a given construct definition
            # we can tap into that here with .node.id to retrieve that same value.
            for bucket in constructs:
                self.environment[
                    bucket.node.id.replace(conformed_prefix, "")
                    .replace("-", "_")
                    .upper()
                ] = bucket.bucket_name


@dataclass
class LambdaLayerConfigs(DynamicCDKConfigs):
    """
    Configuration properties for Lambda Layers. See `cdk_configs/resource_properties.py
     - LambdaFunctionConfigs for more information on the use of these classes"

    Parameters:
        common [CDKProps] (from parent): The CDKProps child class this resource
            will use as common properties. It must be a LambdaLayer specific one
        layer_version_name [str]: Name of this layer.
        description [str]: a short description of this layer.
        code [Path]: the directory path to the layer zip.

    Methods
        props() (from parent):
            returns a dictionary of properties to be slotted into the kwargs of a Lambda
            resource.
    """

    layer_version_name: str
    description: str
    code: Union[Path, aws_lambda.AssetCode]

    def __post_init__(self):
        super().__post_init__()

    def update_with_deployment_specific_values(
        self, base_directory: Path, name_prefix: str
    ):
        """
        Parameters:
            base_directory: A Path or Path Like object for the location of the
            layer zip.
            name_prefix: [str] - The resource name prefixed with the deployment values.
        """
        self._prefix_name(name_prefix)

        if isinstance(self.code, Path):
            self.code = os.join(base_directory, self.code)

        if not isinstance(self.code, aws_lambda.AssetCode):
            self.code = aws_lambda.AssetCode(os.path.join(base_directory, self.code))

        self._necessary_values_set = True

    def props(self, base_directory: Path, name_prefix: str) -> dict:
        """
        Parameters:
            base_directory: A Path or Path Like object for the location of the
            layer zip.
            name_prefix: [str] - The resource name prefixed with the deployment values.
        """
        self.update_with_deployment_specific_values(base_directory, name_prefix)
        return super().props()


##########################################
#   Codebuilds                           #
##########################################


@dataclass
class CodebuildConfigs(DynamicCDKConfigs):
    project_name: str
    description: str
    build_spec: str
    environment_variables: Union[
        TestingCodebuildEnvVariables, DeploymentCodebuildEnvVariables
    ]
    logging: dict = field(init=False, default=None)

    def __post_init__(self):
        super().__post_init__()

    def update_with_deployment_specific_values(
        self,
        log_group: logs.LogGroup,
        role: iam.Role,
        name_prefix: str,
        use_prod_values: bool = False,
        cross_account: bool = False,
    ):
        """
        Parameters:
            log_group: [aws_logs.LogGroup] the log group to assign to this codebuild.
            role: [aws_iam.Role] - the role this codebuild needs, if any.
            name_prefix: [str] - The resource name prefixed with the deployment values.
            use_prod_values [bool] to us the prod values or not. Safest method is to pass
                in the DeploymentProperties.USING_PROD_VALUES value.
            cross_account: [bool] - If this deployment is a cross account deployment or not.
        """
        self._prefix_name(name_prefix)

        self.build_spec = codebuild.BuildSpec.from_source_filename(
            filename=self.build_spec
        )

        self._build_codebuild_env_variables(use_prod_values, cross_account)

        self.logging = {"cloud_watch": {"log_group": log_group}}
        self.role = role
        self._necessary_values_set = True

    def props(
        self,
        log_group: logs.LogGroup,
        role: iam.Role,
        name_prefix: str,
        use_prod_values: bool = False,
        cross_account: bool = False,
    ) -> dict:
        """
        Parameters:
            log_group: [aws_logs.LogGroup] the log group to assign to this codebuild.
            role: [aws_iam.Role] - the role this codebuild needs, if any.
            name_prefix: [str] - The resource name prefixed with the deployment values.
            use_prod_values [bool] to us the prod values or not. Safest method is to pass
                in the DeploymentProperties.USING_PROD_VALUES value.
            cross_account: [bool] - If this deployment is a cross account deployment or not.
        """
        self.update_with_deployment_specific_values(
            log_group, role, name_prefix, use_prod_values, cross_account
        )
        return super().props()

    def _build_codebuild_env_variables(
        self, use_prod_values: bool, cross_account: bool
    ):
        """
        Specific functionality for building a codebuild env variable map for CDK
        """
        env_vars = {
            key: codebuild.BuildEnvironmentVariable(value=variable)
            for key, variable in self.environment_variables.__dict__.items()
            if not key.startswith("_") and variable is not None
        }

        if use_prod_values and env_vars.get("USE_PROD_VALUES") is not None:
            env_vars["USE_PROD_VALUES"] = codebuild.BuildEnvironmentVariable(
                value=f"-c {ContextTag.is_prod}=True"
            )

        if cross_account and env_vars.get("PROD_ASSUME_ROLE") is not None:
            env_vars["PROD_ASSUME_ROLE"] = codebuild.BuildEnvironmentVariable(
                value=DeploymentFileLocation.ASSUME_CROSS_ACCOUNT_ROLE
            )

        self.environment_variables = env_vars


@dataclass
class TestingCodebuildEnvVariables:
    SCRIPT: str
    SECRET_LOCATION: str
    TESTING_TYPE: str


@dataclass
class DeploymentCodebuildEnvVariables:
    PROD_ASSUME_ROLE: str
    CDK_ACTION: str
    STACK_TO_DEPLOY: str
    DEPLOYMENT_TAG: str
    USE_PROD_VALUES: str


##########################################
#   Logging and Cloudwatch               #
##########################################


@dataclass
class LogGroupConfigs(DynamicCDKConfigs):
    removal_policy: cdk.RemovalPolicy
    retention: logs.RetentionDays = field(init=False)

    def __post_init__(self):
        super().__post_init__()

    def update_with_deployment_specific_values(
        self, use_prod_values: bool, log_group_name: str
    ):
        """
        Parameters:
            use_prod_values [bool] to us the prod values or not. Safest method is to pass
                in the DeploymentProperties.USING_PROD_VALUES value.
            log_group_name: [str] - The resource name prefixed with the deployment values.
                Unlike other DynamicCDKConfig child classes, this one does not have a name
                property on instantiation. THis is because the name is dependant on the
                resource the log group is being attached too, so needs to be set at the
                time of the log group creation.
        """

        deployment_values = (
            ProductionProductProperties if use_prod_values else DevProductProperties
        )
        self.log_group_name = log_group_name

        self.retention = deployment_values.LOG_GROUP_RETENTION

        self._necessary_values_set = True

    def props(self, use_prod_values: bool, log_group_name: str) -> dict:
        """
        Parameters:
            use_prod_values [bool] to us the prod values or not. Safest method is to pass
                in the DeploymentProperties.USING_PROD_VALUES value.
            log_group_name: [str] - The resource name prefixed with the deployment values.
                Unlike other DynamicCDKConfig child classes, this one does not have a name
                property on instantiation. THis is because the name is dependant on the
                resource the log group is being attached too, so needs to be set at the
                time of the log group creation.
        """
        self.update_with_deployment_specific_values(use_prod_values, log_group_name)
        return super().props()

    @classmethod
    def build_log_group_path(
        cls,
        product_name: Optional[str] = None,
        category: Optional[str] = None,
        resource_type: str = None,
        resource_prefix: Optional[str] = None,
        resource_name: str = None,
        **kwargs,
    ) -> str:
        """
        Builds a log group path of format
            product_name/category/[additional kwargs]/resource_type/resource_prefix-resource_name

        Classmethod, so is available even before instantiation.

        Parameters:
            product_name: Optional[str] - The name of the Product. Useful if more than
                one product exists in the same AWS account.
            category: Optional[str] - A qualifier, su ch as Pipeline or Tools.
            resource_type:str - The Resource type, such as codebuild or step_functions
            resource_prefix: Optional[str] - A prefix to help differentiate between
                multiple deployed environments in the same account.
            resource_name:str - The name of the resource this log group is attached too.

            any other non-predefined kwargs can be included and they will be placed between
            category and resource_type allowing custom sub categories.


        Aids in consistency in log group names for easier sorting, querying, and automation.
        """
        prefixed_name = (
            f"{resource_prefix}-{resource_name}"
            if resource_prefix is not None
            else resource_name
        )
        known_keys = [
            "product_name",
            "category",
            "resource_type",
            "resource_prefix",
            "resource_name",
        ]
        additional_keywords = [
            value
            for key, value in kwargs.items()
            if key not in known_keys and value is not None
        ]

        path_values = list(
            filter(
                None,
                [
                    *[product_name, category],
                    *additional_keywords,
                    *[resource_type, prefixed_name],
                ],
            )
        )

        return "/".join(path_values).replace(" ", "_")


##########################################
#   Storage - Dynamodb, S3, ect          #
##########################################


@dataclass
class DynamoDbConfigs(DynamicCDKConfigs):
    """
    Properties class for a DynamoDB - Note: Because the best practice for dynamo usually
    involves both a pk and an sk, those values are defined as part of the DynamoProps
    classes in common_configs.
    """

    table_name: str
    time_to_live_attribute: Optional[str] = field(default=None)
    stream: Optional[dynamodb.StreamViewType] = field(default=None)
    removal_policy: cdk.RemovalPolicy = field(init=False)

    def __post_init__(self):
        super().__post_init__()

    def update_with_deployment_specific_values(
        self, prod_deployment: bool, name_prefix: str
    ):
        """
        Parameters:
            prod_deployment [bool] if this is a prod deployment or not - Safest way to set
                is to use DeploymentProperties.PROD_DEPLOYMENT.
            name_prefix: [str] - The resource name prefixed with the deployment values.
        """
        deployment_properties = (
            ProductionProductProperties if prod_deployment else DevProductProperties
        )
        self._prefix_name(name_prefix)
        self.removal_policy = deployment_properties.DYNAMO_REMOVAL_POLICY
        self._necessary_values_set = True

    def props(self, prod_deployment: bool, name_prefix: str) -> dict:
        """
        Parameters:
            prod_deployment [bool] if this is a prod deployment or not - Safest way to set
                is to use DeploymentProperties.PROD_DEPLOYMENT.
            name_prefix: [str] - The resource name prefixed with the deployment values.
        """
        self.update_with_deployment_specific_values(prod_deployment, name_prefix)
        return super().props()


@dataclass
class DynamoDBGlobalSecondaryIndexConfigs(DynamicCDKConfigs):
    """
    Properties for a Global Secondary Index.

    Note: refrain from using too many GSI's. If you find you need more than 1, you should
    re-evaluate how the data is being stored in dynamo and your access patterns around that.

    Can take different types for the pk and sk if they are not dynamodb.AttributeType.STRING



    """

    index_name: str
    partition_key: str
    sort_key: str
    projection_type: dynamodb.ProjectionTyp = field(default=dynamodb.ProjectionType.ALL)
    partition_type: dynamodb.Attribute = field(default=dynamodb.AttributeType.STRING)
    sort_type: dynamodb.Attribute = field(default=dynamodb.AttributeType.STRING)

    def __post_init__(self):
        self.partition_key = dynamodb.Attribute(
            name=self.partition_key, type=self.partition_type
        )
        self.sort_key = dynamodb.Attribute(name=self.sort_key, type=self.sort_type)

        self.partition_type = None
        self.sort_type = None
        self._necessary_values_set = True
        super().__post_init__()


@dataclass
class S3BucketConfigs(DynamicCDKConfigs):
    bucket_name: str
    lifecycle_rules: Optional[List[s3.LifecycleRule]] = field(init=False, default=None)
    auto_delete_objects: bool = field(init=False, default=False)
    removal_policy: bool = field(init=False, default=None)

    def __post_init__(self):
        super().__post_init__()

    def update_with_deployment_specific_values(
        self, prod_deployment: bool, use_prod_values: bool, name_prefix: str
    ):
        """
        Parameters:
            prod_deployment: [bool] - If this is a prod deployment (and so retaining
                data). Safest way to set is to use DeploymentProperties.PROD_DEPLOYMENT
            use_prod_values: [bool] - If lifecycle rules should be the prod rules or not.
                Safest way to set is to use DeploymentProperties.USING_PROD_VALUES.
            name_prefix: [str] - The resource name prefixed with the deployment values.
        """

        deployment_properties = (
            ProductionProductProperties if prod_deployment else DevProductProperties
        )
        deployment_set_values = (
            ProductionProductProperties if use_prod_values else DevProductProperties
        )

        self._prefix_name(name_prefix)
        self.bucket_name = self.bucket_name.lower()
        self.removal_policy = deployment_properties.S3_REMOVAL_POLICY
        self.auto_delete_objects = not prod_deployment
        self.lifecycle_rules = [
            s3.LifecycleRule(
                id=f"{self.bucket_name}-{deployment_set_values.S3_LIFECYCLE_DURATION}-Days-Lifecycle",
                expiration=cdk.Duration.days(
                    deployment_set_values.S3_LIFECYCLE_DURATION
                ),
            )
        ]
        self._necessary_values_set = True

    def props(
        self, prod_deployment: bool, use_prod_values: bool, name_prefix: str
    ) -> dict:
        """
        Parameters:
            prod_deployment: [bool] - If this is a prod deployment (and so retaining
                data). Safest way to set is to use DeploymentProperties.PROD_DEPLOYMENT
            use_prod_values: [bool] - If lifecycle rules should be the prod rules or not.
                Safest way to set is to use DeploymentProperties.USING_PROD_VALUES.
            name_prefix: [str] - The resource name prefixed with the deployment values.
        """
        self.update_with_deployment_specific_values(
            prod_deployment, use_prod_values, name_prefix
        )
        return super().props()


##########################################
#   Api Configs                          #
##########################################


@dataclass
class RestApiConfigs(DynamicCDKConfigs):
    rest_api_name: str
    retain_deployments: bool

    def __post_init__(self):
        self._necessary_values_set = True
        super().__post_init__()


@dataclass
class RestApiResourceConfigs(DynamicCDKConfigs):
    path_part: str
    parent: apigateway.RestApi = field(init=False)

    def __post_init__(self):
        super().__post_init__()

    def props(self, parent: apigateway.Resource) -> dict:
        """
        Set the parent as well as part of the props.
        """

        self.parent = parent
        self._necessary_values_set = True
        return super().props()


@dataclass
class RestApiMethodConfigs(DynamicCDKConfigs):
    """
    Creates a Method (Get, Post, ect) on a given resource

    Parameters:
        http_method: [str], "POST", "GET", "OPTIONS" or others
        x_lambda_integration: [str] - name of the lambda this API connects too.

    NOTE:
        as a demonstration option this config class assumes a few things:
        1. The method will be connecting to a lambda as a PROXY connection.
        2. There is no API Key required.
        3. JSON in JSON out.
        4. No handling of additional error codes.

        It may not be worth it with API's to use a config class and instead leave the
        API stacks as a direct CDK depending on how complex your API patterns are.
    """

    http_method: str
    x_lambda_integration: str
    options: apigateway.MethodOptions = field(init=False)
    integration: apigateway.LambdaIntegration = field(init=False)
    resource: apigateway.Resource = field(init=False)

    def __post_init__(self):
        self.options = apigateway.MethodOptions(
            api_key_required=False, method_responses=[json_200_method_response]
        )
        super().__post_init__()

    def props(self, resource: apigateway.Resource, lambda_mapping: dict) -> dict:
        """
        Parameters:
            resource: [aws_cdk.aws_apigateway.Resource] The RestAPI Gateway Resource
                that this method attaches too.
            lambda_mapping: [Dict]: The mapping of all the lambdas. Used in conjunction
                with x_lambda_integration to attach the lambda as a proxy.
        """
        self.resource = resource

        self.integration = apigateway.LambdaIntegration(
            handler=lambda_mapping[self.x_lambda_integration],
            proxy=True,
            integration_responses=[json_200_integration_response],
        )
        self._necessary_values_set = True
        return super().props()
