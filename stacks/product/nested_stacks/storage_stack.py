import aws_cdk as cdk
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_dynamodb as dynamodb
from cdk_configs.product_properties.common_props import DeploymentProperties
from cdk_configs.resource_names import ProductDynamodbName
from cdk_configs.resource_configurations.constructs import (
    S3BucketConfigs,
    DynamoDbConfigs,
)
from common.aws.dynamodb.constants import KeyName
from cdk_configs.resource_configurations.storage_configs import (
    PRODUCT_DYNAMO_DBS,
    PRODUCT_DYNAMO_SECONDARY_INDEXES,
    PRODUCT_S3_BUCKETS,
)
from typing import Dict
from constructs import Construct


class ProductStorage(cdk.NestedStack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        deployment_properties: DeploymentProperties,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        props = deployment_properties

        self.bucket_mapping: Dict[str, s3.Bucket] = {}
        self.dynamo_mapping: Dict[str, dynamodb.Table] = {}

        # Type Annotation
        bucket_config: S3BucketConfigs
        for name, bucket_config in PRODUCT_S3_BUCKETS.items():

            self.bucket_mapping[name] = s3.Bucket(
                self,
                name,
                **bucket_config.props(
                    prod_deployment=props.PROD_DEPLOYMENT,
                    use_prod_values=props.USING_PRODUCTION_VALUES,
                    name_prefix=props.prefix_tag(),
                )
            )

        dynamo_config: DynamoDbConfigs
        for name, dynamo_config in PRODUCT_DYNAMO_DBS.items():
            table = dynamodb.Table(
                self,
                name,
                **dynamo_config.props(
                    prod_deployment=props.PROD_DEPLOYMENT,
                    name_prefix=props.prefix_tag(),
                )
            )
            table.add_global_secondary_index(
                **PRODUCT_DYNAMO_SECONDARY_INDEXES[
                    ProductDynamodbName.INVERTED_GLOBAL_INDEX
                ].props()
            )
            self.dynamo_mapping[name] = table
