from cdk_configs.resource_configurations.constructs import (
    RestApiConfigs,
    RestApiMethodConfigs,
    RestApiResourceConfigs,
)
from cdk_configs.resource_names import ProductApiName, ProductLambdaName
from cdk_configs.resource_configurations.common_configs import NoCommonConfigs

PRODUCT_REST_API = RestApiConfigs(
    common=NoCommonConfigs,
    rest_api_name=ProductApiName.API_NAME,
    retain_deployments=True,
)

PRODUCT_API_VERSIONS = {
    ProductApiName.VERSION_ONE: RestApiResourceConfigs(
        common=NoCommonConfigs, path_part=ProductApiName.VERSION_ONE
    )
}

# These methods will be deployed on each version
PRODUCT_API_RESOURCES = {
    ProductApiName.HELLO_RESOURCE: {
        "resource": RestApiResourceConfigs(
            common=NoCommonConfigs, path_part=ProductApiName.HELLO_RESOURCE
        ),
        "methods": {
            "POST": RestApiMethodConfigs(
                common=NoCommonConfigs,
                http_method="POST",
                x_lambda_integration=ProductLambdaName.HELLO_WORLD,
            ),
            "OPTIONS": RestApiMethodConfigs(
                common=NoCommonConfigs,
                http_method="OPTIONS",
                x_lambda_integration=ProductLambdaName.HELLO_WORLD,
            ),
        },
    },
    ProductApiName.GOODBYE_RESOURCE: {
        "resource": RestApiResourceConfigs(
            common=NoCommonConfigs, path_part=ProductApiName.GOODBYE_RESOURCE
        ),
        "methods": {
            "POST": RestApiMethodConfigs(
                common=NoCommonConfigs,
                http_method="GET",
                x_lambda_integration=ProductLambdaName.HELLO_WORLD,
            )
        },
    },
}
