import aws_cdk as cdk
from cdk_configs.default_tags import DefaultTags
from cdk_configs.product_properties.common_props import DeploymentProperties
from cdk_configs.resource_names import DeploymentResourceName
from stacks.pipeline.pipeline_stack import Pipeline
from stacks.product.product_stack import Product


# Initializes the cdk app process
app = cdk.App()

props = DeploymentProperties(app)

default_tags = DefaultTags(deployment_properties=props)


####################################
# Product Stack                    #
####################################

product = Product(
    app,
    f"{props.prefix_tag()}-{DeploymentResourceName.MAIN_STACK}",
    env=props.aws_environment,
    deployment_properties=props,
)

default_tags.apply(product)


####################################
# Pipeline Stacks                  #
####################################

pipeline = Pipeline(
    app,
    f"Pipeline-{props.prefix_tag()}",
    env=props.aws_environment,
    deployment_properties=props,
)

default_tags.apply(pipeline)

####################################
# Tool Stacks                      #
####################################

# this is the actual magic here, it synths the stacks
app.synth()

print("***Deployment Properties:")
print(f"   **deploy_tag:       {props.DEPLOYMENT_TAG}")
print(f"   **naming prefix:    {props.prefix_tag()}")
print(f"   **user:             {props._user}")
print(f"   **commit_sha:       {props._commit_sha}")
print(f"   **prod_status:      {props.PROD_DEPLOYMENT}")
print(f"   **account:          {app.account}")
print(f"   **region:           {app.region}")
print(f"   **deployed at:      {props.DEPLOYMENT_DATE}")
