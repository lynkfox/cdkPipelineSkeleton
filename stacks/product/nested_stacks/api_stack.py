import aws_cdk as cdk
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as r53_targets
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_certificatemanager as certmanager
from constructs import Construct
from typing import Dict
from aws_cdk.aws_lambda import IFunction
from cdk_configs.product_properties.common_props import DeploymentProperties
from cdk_configs.resource_configurations.constructs import (
    RestApiResourceConfigs,
    RestApiMethodConfigs,
)
from cdk_configs.resource_configurations.api_configs import (
    PRODUCT_REST_API,
    PRODUCT_API_VERSIONS,
    PRODUCT_API_RESOURCES,
)
from cdk_configs.product_properties.pipeline_and_deployment_props import (
    DeploymentSecretKey,
)
from cdk_configs.resource_names import ProductApiName


class ProductApi(cdk.NestedStack):
    def __init__(
        self,
        scope: Construct,
        id: str,
        deployment_properties: DeploymentProperties,
        lambda_mapping: Dict[str, IFunction],
        **kwargs,
    ) -> None:
        super().__init__(scope, id, **kwargs)

        props = deployment_properties

        self.api = apigateway.RestApi(
            self, ProductApiName.API_NAME, **PRODUCT_REST_API.props()
        )

        versions = {}
        # Type Hint Annotation
        version: RestApiResourceConfigs
        for name, version in PRODUCT_API_VERSIONS.items():
            versions[name] = apigateway.Resource(
                self, name, **version.props(self.api.root)
            )

        # NOTE ON THE FOLLOWING:
        # If you end up with a lot of versions and or a lot of resources/methods this
        # can very quickly get out of hand. It would be better to divide your versions
        # into multiple nested stacks then in order to keep under the 500 resource limit
        # of a given Stack/NestedStack
        #
        # Note the Second:
        # The resources/methods are not saved anywhere. If you need them for something
        # outside this loop, then you'll have to map them as part of the loop.

        # Type Hint Annotation
        resource: Dict[str, any]
        for name, resource in PRODUCT_API_RESOURCES.items():
            resource_config: RestApiResourceConfigs
            method_configs = Dict[str, any]

            resource_config = resource.get("resource")
            method_configs = resource.get("methods")

            for version in versions.values():
                # construct the resource for each version of the api sub-roots
                resource_construct = apigateway.Resource(
                    self, name, **resource_config.props(version)
                )

                method: RestApiMethodConfigs
                for method_name, method in method_configs.items():
                    # construct each method for that given resource
                    # method name will be something like POST or GET or OPTIONS
                    apigateway.Method(
                        self,
                        f"{name}-{method_name}",
                        **method.props(
                            resource=resource_construct, lambda_mapping=lambda_mapping
                        ),
                    )

        ######################################
        # Domain Name                        #
        ######################################

        domain_name = apigateway.DomainName(
            self,
            "PLQuotingDomain",
            certificate=certmanager.Certificate.from_certificate_arn(
                self,
                "API Cert",
                certificate_arn=props.secret(DeploymentSecretKey.DOMAIN_CERT),
            ),
            domain_name=props.COMPLETE_DOMAIN_NAME,
        )

        domain_name.add_base_path_mapping(
            target_api=self.api, stage=self.api.deployment_stage
        )

        route53_host_zone = route53.HostedZone.from_hosted_zone_attributes(
            self,
            "Route53HostZone",
            hosted_zone_id=props.secret(DeploymentSecretKey.HOST_ZONE_ID),
            zone_name=props.secret(DeploymentSecretKey.HOST_ZONE_NAME),
        )

        route53.ARecord(
            self,
            "DomainAliasRecord",
            zone=route53_host_zone,
            target=route53.RecordTarget.from_alias(
                r53_targets.ApiGatewayDomain(domain_name)
            ),
            record_name=props.COMPLETE_DOMAIN_NAME,
        )

        # You may need/want to add AAAA Records or others here as well
