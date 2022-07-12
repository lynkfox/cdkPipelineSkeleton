from datetime import datetime

import aws_cdk as cdk
import git
from cdk_configs.product_properties.common_props import (
    DeploymentProperties,
    ProductSetting,
)


class DefaultTags(dict):
    """
    DefaultTags class for tagging AWS objects. - Provided by Platform Services

    https://stateautoinsurance.atlassian.net/wiki/spaces/PS/pages/2295070763/AWS+Resource+Tagging+Standard

    A dict of {name:value} pairs for each tag in our default collection of tags

    Parameters:
        deployment_properties [cdk_configuration.common_props.DeploymentProperties]: A
            Data object of common properties needed for all stacks.

    Methods:
        apply(target: cdk.app): applies the tags contained within to the targeted stack
    """

    def apply(self, target):
        """Apply the tags to the target."""
        for key, value in self.items():

            if value == "" or value is None:
                continue
            cdk.Tags.of(target).add(key, value)

    def __init__(self, deployment_properties: DeploymentProperties):
        self.props = deployment_properties
        self.owner = ProductSetting.PRODUCT_TEAM
        self.is_production = (
            "True" if deployment_properties.PROD_DEPLOYMENT else "False"
        )
        self.environment = deployment_properties.DEPLOYMENT_TAG
        self.name_tag = deployment_properties.prefix_tag()
        self.product_name = ProductSetting.PRODUCT_TAG
        self.repo = git.Repo(search_parent_directories=True)
        try:
            self.branch_name = self.repo.active_branch.name
        except Exception:
            self.branch_name = (
                ProductSetting.GITHUB_MAIN_BRANCH
                if deployment_properties.PROD_DEPLOYMENT
                else ProductSetting.GITHUB_DEV_BRANCH
            )

        self.commit_hash = self.repo.head.commit.hexsha
        deployment_properties._commit_hash = self.commit_hash
        self.deployed_by = deployment_properties._user

        self.datetime_format = "%Y-%m-%dT%H:%M:%S:%fZ"
        self.build_tags()

    def build_tags(self):
        """Return a dict of {tag_name:tag_value} tags."""
        for name, value in {
            "sa:owner": self.owner,
            "sa:is-production": str(self.is_production),
            "sa:environment": self.environment,
            "sa:project-name": self.product_name,
            "sa:project-url": f"{ProductSetting.GITHUB_ENTERPRISE_URL}/{ProductSetting.GITHUB_ORG}/{ProductSetting.GITHUB_REPO}",
            "sa:project-branch": self.branch_name,
            "sa:commit-sha": self.commit_hash,
            "sa:commit-author": self.repo.head.commit.author.name.replace(",", "")
            .replace("\\", "")
            .replace("SAI", ""),
            "sa:deploy-datetime": self.props.DEPLOYMENT_DATE,
            "sa:deployed-by": self.deployed_by,
            f"sa:{ProductSetting.PRODUCT_TAG.lower()}:name-prefix": self.name_tag,
        }.items():
            print(f"***Tag {name} = {value}")
            self[name] = value
