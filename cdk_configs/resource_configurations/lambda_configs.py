from cdk_configs.resource_configurations.constructs import (
    LambdaFunctionConfigs,
    LambdaLayerConfigs,
)
from cdk_configs.resource_names import DeploymentResourceName, ProductLambdaName
from cdk_configs.resource_configurations.common_configs import (
    PipelineLambdaFunctionConfigs,
    PipelineLayerConfigs,
    ProductLambdaFunctionConfigs,
    ProductLayerConfigs,
)


PIPELINE_LAMBDAS = {
    DeploymentResourceName.JIRA_STATUS: LambdaFunctionConfigs(
        common=PipelineLambdaFunctionConfigs,
        function_name=DeploymentResourceName.JIRA_STATUS,
        location="jira_status.jira_status_lambda.lambda_handler",
    ),
    DeploymentResourceName.GITHUB_TAG: LambdaFunctionConfigs(
        common=PipelineLambdaFunctionConfigs,
        function_name=DeploymentResourceName.GITHUB_TAG,
        location="github_tag.github_tag_lambda.lambda_handler",
    ),
    DeploymentResourceName.SEEK_APPROVAL: LambdaFunctionConfigs(
        common=PipelineLambdaFunctionConfigs,
        function_name=DeploymentResourceName.SEEK_APPROVAL,
        location="snow_approval.send_snow_ticket_lambda.lambda_handler",
    ),
    DeploymentResourceName.APPROVE_PIPELINE: LambdaFunctionConfigs(
        common=PipelineLambdaFunctionConfigs,
        function_name=DeploymentResourceName.APPROVE_PIPELINE,
        location="snow_approval.approve_pipeline_lambda.lambda_handler",
    ),
}

PIPELINE_LAYERS = {
    DeploymentResourceName.PIPELINE_LAYER: LambdaLayerConfigs(
        common=PipelineLayerConfigs,
        layer_version_name=DeploymentResourceName.PIPELINE_LAYER,
        description=f"Dependencies for Pipeline Lambdas",
        code="pipeline_layer.zip",
    )
}

PRODUCT_LAMBDAS = {
    ProductLambdaName.HELLO_WORLD: LambdaFunctionConfigs(
        common=ProductLambdaFunctionConfigs,
        function_name=ProductLambdaName.HELLO_WORLD,
        location="hello_world.hello_world_lambda.lambda_handler",
        # Product Lambda stack automatically starts paths at ./aws_lambda_functions/
        x_link_to_bucket=True,
    ),
    ProductLambdaName.GOODBYE_FOR_NOW: LambdaFunctionConfigs(
        common=ProductLambdaFunctionConfigs,
        function_name=ProductLambdaName.GOODBYE_FOR_NOW,
        location="goodbye_for_now.goodbye_for_now_lambda.lambda_handler",
        x_link_to_dynamo=True,
    ),
}

PRODUCT_LAYERS = {
    ProductLambdaName.COMMON_LAYER: LambdaLayerConfigs(
        common=ProductLayerConfigs,
        layer_version_name=ProductLambdaName.COMMON_LAYER,
        description=f"Common Functions shared between Lambdas",
        code="common_layer.zip",  # Product Lambda stack automatically starts paths at ./aws_lambda_functions/
    )
}
