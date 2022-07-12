from dataclasses import dataclass
import aws_cdk as cdk
from aws_cdk import aws_logs as logs

########################################################################################
#
# Note: Proper CICD and DevOps practices state NO LONG TERM ENVIRONMENTS / BRANCHES.
# Technically, having a prod and a dev branch / environment violates this rule, but
# this is one that its kinda okay to get away with as a necessary evil in our current
# company maturity.
#
# However.
#
# At no point is it acceptable to add another long living environment - So, at no point
# is it needed to add any more EnvironmentProperties classes to this file. If you need
# temporary environments, use the deployment options to deploy a test env and utilize
# the necessary flags to use the appropriate values for your test.
#
# Such environments have a mandate to be destroyed when they are done. On average, it is
# probably a good idea that no such environment last more than 3 days.
#
########################################################################################


@dataclass(frozen=True)
class CommonProductProperties:
    """
    Properties that are mostly static and common no matter the deployment environment
    """


@dataclass(frozen=True)
class ProductionProductProperties:
    """
    Properties that are mostly static and specific to deployment in the Production Env
    (triggered with a combination of DeploymentProperties.PROD_DEPLOYMENT and or
    DeploymentProperties.USING_PROD_VALUES)

    If the value is the same between environments, put it in Common.

    The name of the property must be identical between this class and the Dev version.
    """

    # USING_PROD_VALUES is true will set these:
    S3_LIFECYCLE_DURATION: int = 90

    # PROD_DEPLOYMENT must be true in order to set these:
    S3_REMOVAL_POLICY: cdk.RemovalPolicy = cdk.RemovalPolicy.RETAIN
    DYNAMO_REMOVAL_POLICY: cdk.RemovalPolicy = cdk.RemovalPolicy.SNAPSHOT
    LOG_GROUP_RETENTION: logs.RetentionDays = logs.RetentionDays.ONE_MONTH
    DOMAIN_NAME = "msp0099.stateauto.com"


@dataclass(frozen=True)
class DevProductProperties:
    """
    Properties that are mostly static and specific to deployment in the Dev Env
    """

    S3_LIFECYCLE_DURATION: int = 7
    S3_REMOVAL_POLICY: cdk.RemovalPolicy = cdk.RemovalPolicy.DESTROY
    DYNAMO_REMOVAL_POLICY: cdk.RemovalPolicy = cdk.RemovalPolicy.DESTROY
    LOG_GROUP_RETENTION: logs.RetentionDays = logs.RetentionDays.ONE_WEEK
    DOMAIN_NAME = "msd0099.stateauto.com"
