import aws_cdk as cdk
from cdk_configs.product_properties.common_props import DeploymentProperties
from constructs import Construct
from stacks.product.nested_stacks.api_stack import ProductApi
from stacks.product.nested_stacks.lambda_stack import ProductLambdas
from stacks.product.nested_stacks.storage_stack import ProductStorage
from stacks.product.nested_stacks.api_stack import ProductApi
from cdk_configs.product_properties.common_props import CloudformationOutputs


class Product(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        deployment_properties: DeploymentProperties,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        props = deployment_properties

        storage = ProductStorage(self, "ProductStorage", deployment_properties=props)

        product_lambdas = ProductLambdas(
            self,
            "ProductLambdas",
            deployment_properties=props,
            dynamodbs=storage.dynamo_mapping,
            buckets=storage.bucket_mapping,
        )

        api_stack = ProductApi(
            self,
            "ProductAPI",
            deployment_properties=props,
            lambda_mapping=product_lambdas.lambda_mapping,
        )

        #######################################################
        # Output some resource names for the Pipeline to use  #
        #######################################################

        cdk.CfnOutput(self, CloudformationOutputs.API_ENDPOINT, value=api_stack.api.url)
        cdk.CfnOutput(
            self, CloudformationOutputs.DOMAIN_NAME, value=props.COMPLETE_DOMAIN_NAME
        )
