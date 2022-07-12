import os
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_lambda
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_s3 as s3
from constructs import Construct
from typing import Dict
from cdk_configs.product_properties.common_props import DeploymentProperties
from cdk_configs.resource_configurations.constructs import (
    LambdaLayerConfigs,
    LambdaFunctionConfigs,
)
from cdk_configs.resource_names import ProductBucketName, ProductDynamodbName
from cdk_configs.resource_configurations.lambda_configs import (
    PRODUCT_LAMBDAS,
    PRODUCT_LAYERS,
)


base_directory = os.path.join(Path(__file__).parents[3], "aws_lambda_functions")


class ProductLambdas(cdk.NestedStack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        deployment_properties: DeploymentProperties,
        dynamodbs: Dict[str, dynamodb.Table],
        buckets: Dict[str, s3.Bucket],
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.lambda_mapping = {}
        props = deployment_properties

        ####################################
        # Layers                           #
        ####################################

        product_layers = []
        # TypeHint Annotation
        layer_config: LambdaLayerConfigs
        for name, layer_config in PRODUCT_LAYERS.items():

            product_layers.append(
                aws_lambda.LayerVersion(
                    self, name, **layer_config.props(base_directory, props.prefix_tag())
                )
            )

        ####################################
        # Lambdas                          #
        ####################################

        common_buckets = [buckets[ProductBucketName.YOUR_BUCKET]]
        common_tables = [dynamodbs[ProductDynamodbName.YOUR_DYNAMO]]

        # TypeHint Annotation
        function_config: LambdaFunctionConfigs
        for name, function_config in PRODUCT_LAMBDAS.items():

            self.lambda_mapping[name] = aws_lambda.Function(
                self,
                name,
                layers=product_layers,
                **function_config.props(
                    base_directory=base_directory,
                    name_prefix=props.prefix_tag(),
                    prod_deployment=props.PROD_DEPLOYMENT,
                    dynamodbs=common_tables,
                    buckets=common_buckets,
                ),
            )

            if function_config.x_link_to_bucket:
                for bucket in common_buckets:
                    bucket.grant_read_write(self.lambda_mapping[name])

            if function_config.x_link_to_dynamo:
                for table in common_tables:
                    table.grant_read_write_data(self.lambda_mapping[name])
