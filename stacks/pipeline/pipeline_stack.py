import aws_cdk as cdk
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as pipeline_actions
from aws_cdk import aws_iam as iam
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_sns as sns
from cdk_configs.product_properties.common_props import (
    ProductSetting,
    DeploymentProperties,
)
from cdk_configs.resource_names import DeploymentResourceName
from stacks.pipeline.nested_stacks.codebuild_stacks import PipelineCodebuilds
from stacks.pipeline.nested_stacks.lambda_stack import PipelineLambdas
from constructs import Construct


class Pipeline(cdk.Stack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        deployment_properties: DeploymentProperties,
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        props = deployment_properties
        props.prefix = "Pipeline"
        pipeline_variables = {}

        ####################################
        # Pieces of the Pipeline           #
        ####################################

        props.secret_construct = secretsmanager.Secret.from_secret_name_v2(
            self,
            f"PipelineSecrets",
            secret_name=ProductSetting.DEPLOYMENT_SECRETS,
        )

        pipeline_lambdas = PipelineLambdas(
            self, "PipelineLambdas", deployment_properties=props
        )

        pipeline = codepipeline.Pipeline(
            self,
            "Pipeline",
            pipeline_name=props.prefix_tag(
                resource_name=DeploymentResourceName.PIPELINE,
                custom_prefix=props.prefix,
            ),
            cross_account_keys=props.PROD_DEPLOYMENT,
        )
        # If not using Cross Account Deployment, remove the cross_account_keys kwarg and
        # the below iam policy statement

        if props.PROD_DEPLOYMENT and props.secret_construct is not None:
            pipeline.add_to_role_policy(
                iam.PolicyStatement(
                    actions=["sts:AssumeRole"],
                    resources=[props.secret_construct.secret_arn],
                )
            )

        pipeline.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "kms:Decrypt",
                    "kms:DescribeKey",
                ],
                resources=["*"],
            )
        )
        props.pipeline_role = pipeline.role
        ########
        # SNS Topics
        ########

        sns_notification_topic = sns.Topic(
            self,
            "Topic",
            display_name=props.prefix_tag(
                resource_name=DeploymentResourceName.APPROVAL_SNS_TOPIC,
                custom_prefix=props.prefix,
            ),
        )

        ########
        # Codebuilds
        ########

        pipeline_codebuilds = PipelineCodebuilds(
            self, "PipelineCodebuilds", deployment_properties=props
        )

        ########
        # Stage Artifacts
        ########

        # The Artifact that is pulled into the Pipeline from the Source Stage
        source_artifact = codepipeline.Artifact()

        adhoc_test_env_artifact = codepipeline.Artifact()

        ####################################
        # Pipeline                         #
        ####################################

        ####################################
        # Stages                           #
        ####################################

        ########
        # Source (codestar)
        ########

        source_stage = pipeline_actions.CodeStarConnectionsSourceAction(
            action_name="Repo-CodeStarConnection",
            connection_arn=ProductSetting.CODESTAR_CONNECTION,
            output=source_artifact,
            owner=ProductSetting.GITHUB_ORG,
            repo=ProductSetting.GITHUB_REPO,
            branch=ProductSetting.GITHUB_MAIN_BRANCH
            if props.PROD_DEPLOYMENT
            else ProductSetting.GITHUB_DEV_BRANCH,
            code_build_clone_output=True,
            variables_namespace="SourceVariables",
        )

        pipeline.add_stage(stage_name="Source", actions=[source_stage])

        ###
        # Testings and Deploy Environments stage
        ###

        run_unit_tests = pipeline_actions.CodeBuildAction(
            action_name="Unit-Tests",
            project=pipeline_codebuilds.codebuild_mapping[
                DeploymentResourceName.UNIT_TESTS
            ],
            input=source_artifact,
            outputs=None,
            run_order=1,
        )

        run_integration_tests = pipeline_actions.CodeBuildAction(
            action_name="Integration-Tests",
            project=pipeline_codebuilds.codebuild_mapping[
                DeploymentResourceName.INTEGRATION_TESTS
            ],
            input=source_artifact,
            outputs=None,
            run_order=1,
        )

        deploy_adhoc_test = pipeline_actions.CodeBuildAction(
            action_name="Deploy-Adhoc-Test-Env",
            project=pipeline_codebuilds.codebuild_mapping[
                DeploymentResourceName.DEPLOY_ADHOC
            ],
            input=source_artifact,
            outputs=[adhoc_test_env_artifact],
            run_order=2,
        )

        pipeline_variables["ADHOC_API"] = deploy_adhoc_test.variable("API_DOMAIN")
        pipeline_variables["COMMIT_SHA"] = deploy_adhoc_test.variable("COMMIT_SHA")
        pipeline_variables["DEPLOYMENT_TYPE"] = props.DEPLOYMENT_TAG

        pipeline.add_stage(
            stage_name="Testing",
            actions=[run_unit_tests, run_integration_tests, deploy_adhoc_test],
        )

        ###
        # Contract Tests against an Adhoc environment
        ###
        """
            By Passing in the adhoc_test_env where it was built we can directly access
            the cdk-outputs.json from a script.
        """

        run_contract_tests = pipeline_actions.CodeBuildAction(
            action_name="External-Contract-Tests",
            project=pipeline_codebuilds.codebuild_mapping[
                DeploymentResourceName.CONTRACT_TESTS
            ],
            input=adhoc_test_env_artifact,
            outputs=None,
            run_order=1,
        )

        pipeline.add_stage(stage_name="Contract-Tests", actions=[run_contract_tests])

        ########
        # Manual Approval (SNOW Request through a Lambda?)
        ########

        ###
        # Create API's for SNOW approval (nested stack)
        ###

        # TODO: Api nested stack for SNOW Response to continue the Pipeline

        ###
        # Add the SNOW Approval (currently Manual Approval, will be API/Lambdas)
        ###
        if props.PROD_DEPLOYMENT:
            # TODO: Add snow approval
            snow_approval_request = pipeline_actions.ManualApprovalAction(
                # notify_emails=NOTIFY_EMAILS.replace(" ", "").split(","),
                action_name="Manual-Product-Owner-Approval",
                notification_topic=sns_notification_topic,
                run_order=1,
            )

            pipeline.add_stage(
                stage_name="Product-Owner-Approval",
                actions=[snow_approval_request],
            )

        ########
        # Deploy and Housekeeping
        ########

        deploy_product = pipeline_actions.CodeBuildAction(
            action_name="Deploy-Product",
            project=pipeline_codebuilds.codebuild_mapping[
                DeploymentResourceName.DEPLOY_APP
            ],
            input=source_artifact,
            run_order=1,
        )

        destroy_adhoc_env = pipeline_actions.CodeBuildAction(
            action_name="Cleanup-Test-Env",
            project=pipeline_codebuilds.codebuild_mapping[
                DeploymentResourceName.DESTROY_ADHOC
            ],
            input=adhoc_test_env_artifact,
            outputs=None,
            run_order=1,
        )

        pipeline.add_stage(
            stage_name="Deploy-Product", actions=[deploy_product, destroy_adhoc_env]
        )

        ###
        # Devops Lead Time Tracking
        ###

        lead_time_tracking_steps = [
            pipeline_actions.LambdaInvokeAction(
                lambda_=pipeline_lambdas.lambda_mapping[
                    DeploymentResourceName.GITHUB_TAG
                ],
                action_name="Tag-Commit-With-Prod",
                user_parameters=pipeline_variables,
                run_order=2,
            ),
            pipeline_actions.LambdaInvokeAction(
                lambda_=pipeline_lambdas.lambda_mapping[
                    DeploymentResourceName.JIRA_STATUS
                ],
                action_name="Update-Jira-Card-Status",
                user_parameters=pipeline_variables,
                run_order=999,
            ),
        ]

        pipeline.add_stage(
            stage_name="DevOps-Lead-Time-Tracking", actions=lead_time_tracking_steps
        )
