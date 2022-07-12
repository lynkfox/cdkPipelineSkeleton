from cdk_configs.resource_configurations.constructs import (
    DynamoDbConfigs,
    S3BucketConfigs,
    DynamoDBGlobalSecondaryIndexConfigs,
)
from cdk_configs.resource_names import ProductDynamodbName, ProductBucketName
from cdk_configs.resource_configurations.common_configs import (
    ProductDynamoDbConfigs,
    ProductS3BucketConfigs,
    NoCommonConfigs,
)
from common.aws.dynamodb.constants import AttributeName, KeyName


# Several common properties of these items: Such as Lifcycle Rules and auto_delete are defined in
# cdk_configs/product_properties/product_properties.py - Be sure to look there if you
# can't find what you're looking for here.
#
# (Reason: many of these are environment specific, and the Config class itself handles this.)


# Note: in general you shouldn't need more than one DynamoDB - their nature is that they
# can be used for multiple purposes due to how Partitions work. However, in the interest
# of maintaining consistency, the stacks *can* do multiple dynamos.

PRODUCT_DYNAMO_DBS = {
    ProductDynamodbName.YOUR_DYNAMO: DynamoDbConfigs(
        common=ProductDynamoDbConfigs,
        table_name=ProductDynamodbName.YOUR_DYNAMO,
        time_to_live_attribute=AttributeName.TIME_TO_LIVE,
    )
}

PRODUCT_DYNAMO_SECONDARY_INDEXES = {
    ProductDynamodbName.INVERTED_GLOBAL_INDEX: DynamoDBGlobalSecondaryIndexConfigs(
        common=NoCommonConfigs,
        index_name=ProductDynamodbName.INVERTED_GLOBAL_INDEX,
        partition_key=KeyName.SORT,
        sort_key=KeyName.PARTITION,
    )
}

PRODUCT_S3_BUCKETS = {
    ProductBucketName.YOUR_BUCKET: S3BucketConfigs(
        common=ProductS3BucketConfigs,
        bucket_name=ProductBucketName.YOUR_BUCKET,
    )
}
