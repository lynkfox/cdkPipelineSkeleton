import os
from common.git_integration.git_client import GitClient
from common.constants.environment import Environment
from aws_lambda_powertools import Logger

logger = Logger(child=True)


class TagGit(GitClient):
    def __init__(self, commit_sha: str = None):
        super().__init__()
        self.commit = (
            self.repo.get_commit(sha=commit_sha) if commit_sha is not None else None
        )
        self.tag_name = os.getenv("TAG_VALUE", "Tagged")
        return

    def tag_commit(self, commit_sha: str = None) -> bool:
        """
        Updates the commit sha provided with a Github Tag corresponding to the tag
        value in TAG_VALUE environment variable, defaulting to "Tagged"

        Returns:
            true if successful.
        """

        if commit_sha is None and self.commit is not None:
            commit_sha = self.commit.sha

        if commit_sha is None:  # still none:
            raise Exception("No Commit Sha provided")

        if os.getenv("ENVIRONMENT") == Environment.PROD:

            try:
                tag_exists = self.tag_name in [tag.name for tag in self.repo.get_tags()]

                if tag_exists:
                    reference = self.repo.get_git_ref(f"tags/{self.tag_name}")
                    reference.edit(sha=commit_sha)
                    logger.info(f"Tag Updated to {commit_sha[:7]}: {reference.url}")

                else:
                    response = self.repo.create_git_ref(
                        ref=f"refs/tags/{self.tag_name}", sha=commit_sha
                    )
                    logger.info(f"Tag created at {commit_sha[:7]}: {response.url}")

                return True

            except Exception as e:
                logger.exception("Unable to complete tag")
                return False

        else:
            logger.debug("Non Prod system, not tagging")
            return True


if __name__ == "__main__":
    os.environ = {
        **os.environ,
        **{
            "TAG_VALUE": "prod-commit",
            "ENVIRONMENT": "prod",
            "BRANCH_NAME": "master",
            "TAG": "Prod",
            "SECRET_KEY": "github-token",
            "SECRET_NAME": "plq-pipeline",
            "GITHUB_URL": "https://github.ent.stateauto.com",
            "REPO_NAME": "DigitalLabs/SAQuoting",
        },
    }

    client = TagGit(commit_sha="282b89e8470cdb54ae3580412cb01dbfa90990f4")
    client.tag_commit()
