from dataclasses import dataclass


@dataclass(frozen=True)
class ProductLambdaName:
    """
    Lambda Human readable names
    """

    # Layers
    COMMON_LAYER = "common-utilities"
    # Lambdas
    HELLO_WORLD = "Hello-World"
    GOODBYE_FOR_NOW = "Goodbye-For-Now"
    YOUR_LAMBDA = "Your-Lambda-Name"


@dataclass(frozen=True)
class ProductBucketName:
    """
    s3 Bucket common human readable names. Must be all lower case and use -
    """

    YOUR_BUCKET = "your-bucket-name"


@dataclass(frozen=True)
class ProductDynamodbName:
    """
    DynamoDB common human readable names
    """

    YOUR_DYNAMO = "Your-Dynamo-Name"
    INVERTED_GLOBAL_INDEX = "Inverted"


@dataclass(frozen=True)
class ProductApiName:
    API_NAME = "Your-Api"
    VERSION_ONE = "v1"  # your-domain.com/v1
    HELLO_RESOURCE = "HelloWorld"  # your-domain.com/v1/HelloWorld
    GOODBYE_RESOURCE = "GoodbyeResource"  # your-domain.com/v1/GoodbyeResource


@dataclass(frozen=True)
class DeploymentResourceName:
    """
    Various pipeline/deployment tool resources.
    """

    # Pipeline values
    PIPELINE = "Pipeline"

    # CodeBuilds
    UNIT_TESTS = "Unit-Tests"
    INTEGRATION_TESTS = "Integration-Tests"
    CONTRACT_TESTS = "Contract-Tests"
    DEPLOY_ADHOC = "Deploy-Adhoc-Testing-Env"
    DEPLOY_APP = "Deployment"
    DESTROY_ADHOC = "Destroy-Adhoc-Testing-Env"

    # Pipeline Lambdas
    JIRA_STATUS = "Update-Jira-Status"
    GITHUB_TAG = "Update-Github-Tag"
    SEEK_APPROVAL = "Send-SNOW-Approval-Ticket"
    APPROVE_PIPELINE = "Process-SNOW-Response"

    # Layers
    PIPELINE_LAYER = "Pipeline-Dependencies"
    COMMON_LAYER = "Common-Utilities"

    # Stack Values
    MAIN_STACK = "ProductStack"

    # Misc Resources
    APPROVAL_SNS_TOPIC = "Product-Owner-Approval"
