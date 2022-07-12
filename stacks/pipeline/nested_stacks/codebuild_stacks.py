import aws_cdk as cdk
from cdk_configs.resource_names import DeploymentResourceName
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from cdk_configs.resource_configurations.codebuild_configs import (
    PIPELINE_CODEBUILDS,
    PIPELINE_CODEBUILD_LOG_GROUP,
)
from cdk_configs.resource_configurations.constructs import (
    CodebuildConfigs,
    LogGroupConfigs,
)
from constructs import Construct
from cdk_configs.product_properties.common_props import (
    DeploymentProperties,
    ProductSetting,
)
from cdk_configs.product_properties.pipeline_and_deployment_props import (
    DeploymentSecretKey,
)


class PipelineCodebuilds(cdk.NestedStack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        deployment_properties: DeploymentProperties,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        props = deployment_properties
        self.codebuild_mapping = {}

        # If your Contract Tests or Integration Tests need API keys, uncomment this
        # and the grant_secrets below on Integration Tests

        # secrets = secretsmanager.Secret.from_secret_name_v2(
        #     self, f'Secrets',
        #     secret_name="api-credentials"
        # )

        ####################################
        # Deploy Environments IAM          #
        ####################################

        code_build_role = iam.Role(
            self,
            "CDKDeployCodebuildsRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("codebuild.amazonaws.com"),
                iam.ServicePrincipal("codepipeline.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonAPIGatewayAdministrator"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "SecretsManagerReadWrite"
                ),
            ],
        )

        # Give this role ability to Pass
        code_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[
                    props.pipeline_role.role_arn,
                    f"{props.pipeline_role.role_arn}/*",
                ],
            )
        )

        # Access the pipeline's buckets
        code_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject*", "s3:GetBucket*", "s3:List*"],
                resources=[
                    f"arn:aws:s3:::pipeline-for-{props.DEPLOYMENT_TAG}*",
                    f"arn:aws:s3:::pipeline-for-{props.DEPLOYMENT_TAG}*/*",
                ],
            )
        )

        # Access the encryption key on those buckets
        code_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=["kms:Decrypt", "kms:DescribeKey"],
                resources=[f"arn:aws:kms:{self.region}:*:key/*"],
            )
        )

        code_build_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudformation:CreateStack",
                    "cloudformation:DeleteStack",
                    "cloudformation:DescribeStack*",
                    "cloudformation:GetStackPolicy",
                    "cloudformation:GetTemplate*",
                    "cloudformation:SetStackPolicy",
                    "cloudformation:UpdateStack",
                    "cloudformation:ValidateTemplate",
                ],
                resources=[
                    f"arn:aws:cloudformation:{self.region}:*:stack/{props.prefix}*{DeploymentResourceName.MAIN_STACK}*"
                ],
            )
        )

        if props.PROD_DEPLOYMENT:
            code_build_role.add_to_policy(
                iam.PolicyStatement(
                    actions=["sts:AssumeRole"],
                    resources=[props.secret(DeploymentSecretKey.CROSS_ACCOUNT_ROLE)],
                )
            )

        ####################################
        # Testing                          #
        ####################################

        codebuild_config: CodebuildConfigs
        for name, codebuild_config in PIPELINE_CODEBUILDS.items():
            name_prefix = props.prefix_tag(custom_prefix=props.prefix)
            log_group = PIPELINE_CODEBUILD_LOG_GROUP

            self.codebuild_mapping[name] = codebuild.PipelineProject(
                self,
                name,
                **codebuild_config.props(
                    log_group=logs.LogGroup(
                        self,
                        f"{name_prefix}-{name}-Logs",
                        **log_group.props(
                            props.USING_PRODUCTION_VALUES,
                            LogGroupConfigs.build_log_group_path(
                                product_name=ProductSetting.PRODUCT_TAG,
                                category="pipeline",
                                resource_type="codebuilds",
                                resource_prefix=name_prefix,
                                resource_name=name,
                            ),
                        ),
                    ),
                    role=code_build_role,
                    use_prod_values=props.USING_PRODUCTION_VALUES,
                    cross_account=props.PROD_DEPLOYMENT,
                    name_prefix=name_prefix,
                ),
            )
