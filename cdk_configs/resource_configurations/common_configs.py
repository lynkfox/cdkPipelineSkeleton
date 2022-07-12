from dataclasses import dataclass
from aws_cdk import aws_lambda
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_s3 as s3
import aws_cdk as cdk
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_apigateway as apigateway
from common.aws.dynamodb.constants import KeyName


#######################################################################################
#                                                                                     #
#   Specific types of Resource Properties - such as for Pipeline Lambdas or Layers    #
#   Shouldn't be needed directly in the cdk stacks, but rather utilized through       #
#   one of the DynamicCDKConfigs child classes                                          #
#                                                                                     #
#   These are just examples. The values in these common prop classes are meant to be  #
#   value that are being repeated across multiple resource creations. As such, it     #
#   is entirely possible to add additional properties here, and either remove them    #
#   from the corresponding DynamicCDKConfigs classes, or let these common values        #
#   overwrite the ones in the DynamicCDKConfigs classes. These values have priority     #
#                                                                                     #
#######################################################################################


@dataclass(frozen=True)
class CommonCDKConfigs:
    """
    Child classes of this must implement the same property names as the Construct they
    are representing.
    """

    @classmethod
    def props(cls) -> dict:
        return {
            key: value
            for key, value in cls.__dict__.items()
            if value is not None and (not key.startswith("_" or key.startswith("x_")))
        }


@dataclass(frozen=True)
class NoCommonConfigs(CommonCDKConfigs):
    """
    Special Empty Props dataclass for resources that do not have a common across
    many configuration
    """

    pass


#######################################################################################
#                                                                                     #
#   Specific types of Lambda Properties - such as for Pipeline Lambdas or Stack       #
#   lambdas. Shouldn't be needed directly in the cdk stacks, but rather utilized      #
#   through one of the DynamicCDKConfigs child classes                                  #
#                                                                                     #
#   all children must implement runtime, timeout, and memory                          #
#                                                                                     #
#######################################################################################


@dataclass(frozen=True)
class PipelineLambdaFunctionConfigs(CommonCDKConfigs):
    runtime = aws_lambda.Runtime.PYTHON_3_9
    timeout = cdk.Duration.minutes(2)
    memory_size = 1024


@dataclass(frozen=True)
class ProductLambdaFunctionConfigs(CommonCDKConfigs):
    runtime = aws_lambda.Runtime.PYTHON_3_9
    timeout = cdk.Duration.seconds(30)
    memory_size = 2048


#######################################################################################
#                                                                                     #
#   Specific types of Lambda Layer Properties                                         #
#                                                                                     #
#   all children must implement compatible_runtimes                                   #
#                                                                                     #
#######################################################################################


@dataclass(frozen=True)
class PipelineLayerConfigs(CommonCDKConfigs):
    compatible_runtimes = [aws_lambda.Runtime.PYTHON_3_9]


@dataclass(frozen=True)
class ProductLayerConfigs(CommonCDKConfigs):
    compatible_runtimes = [aws_lambda.Runtime.PYTHON_3_9]


#######################################################################################
#                                                                                     #
#   Specific types of Codebuilds for Pipeline                                         #
#                                                                                     #
#   all children must implement compatible_runtimes                                   #
#                                                                                     #
#######################################################################################


@dataclass(frozen=True)
class PipelineCodebuildConfigs(CommonCDKConfigs):
    environment = codebuild.BuildEnvironment(
        build_image=codebuild.LinuxBuildImage.STANDARD_5_0
    )


#######################################################################################
#                                                                                     #
#   Specific types of Storage types (dynamo, s3) for the Product                      #
#                                                                                     #
#   all dynamo db types must have billing_mode and at least partition_key             #
#                                                                                     #
#######################################################################################


@dataclass(frozen=True)
class ProductDynamoDbConfigs(CommonCDKConfigs):
    billing_mode = dynamodb.BillingMode.PAY_PER_REQUEST
    partition_key = dynamodb.Attribute(
        name=KeyName.PARTITION, type=dynamodb.AttributeType.STRING
    )
    sort_key = dynamodb.Attribute(name=KeyName.SORT, type=dynamodb.AttributeType.STRING)


# No common S3 configs object because most configs are deployment env based and best set
# at cdk time. Using NoCommonConfigs for s3 buckets
ProductS3BucketConfigs = NoCommonConfigs


#######################################################################################
#                                                                                     #
#   Specific configuration options for RestAPIs                                       #
#                                                                                     #
#######################################################################################


json_200_method_response = apigateway.MethodResponse(
    status_code="200",
    response_models={"application/json": apigateway.Model.EMPTY_MODEL},
)

json_200_integration_response = apigateway.IntegrationResponse(
    status_code="200",
    content_handling=apigateway.ContentHandling.CONVERT_TO_TEXT,
    response_templates={"application/json": """$input.path('$.body')\n"""},
)
