import os
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import aws_lambda
from constructs import Construct
from cdk_configs.product_properties.common_props import DeploymentProperties
from cdk_configs.resource_configurations.constructs import (
    LambdaLayerConfigs,
    LambdaFunctionConfigs,
)
from cdk_configs.resource_configurations.lambda_configs import (
    PIPELINE_LAMBDAS,
    PIPELINE_LAYERS,
)


base_directory = os.path.join(Path(__file__).parents[1], "pipeline_lambdas")


class PipelineLambdas(cdk.NestedStack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        deployment_properties: DeploymentProperties,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        self.all_lambdas = []
        self.lambda_mapping = {}
        props = deployment_properties
        lambda_runtime_environment = aws_lambda.Runtime.PYTHON_3_9

        ####################################
        # Layers                           #
        ####################################

        pipeline_layers = []
        # TypeHint Annotation
        layer_config: LambdaLayerConfigs
        for name, layer_config in PIPELINE_LAYERS.items():

            pipeline_layers.append(
                aws_lambda.LayerVersion(
                    self,
                    name,
                    **layer_config.props(
                        base_directory, props.prefix_tag(custom_prefix=props.prefix)
                    ),
                )
            )

        ####################################
        # Lambdas                          #
        ####################################

        # TypeHint Annotation
        function_config: LambdaFunctionConfigs
        for name, function_config in PIPELINE_LAMBDAS.items():
            # set the cdk specific run time values of the function:

            function_config.vpc = props.vpc(self)

            self.lambda_mapping[name] = aws_lambda.Function(
                self,
                name,
                layers=pipeline_layers,
                **function_config.props(
                    base_directory, props.prefix_tag(custom_prefix=props.prefix)
                ),
            )
