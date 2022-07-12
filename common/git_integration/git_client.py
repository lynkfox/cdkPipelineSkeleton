import github as git
from github.Commit import Commit
import urllib3
import os
from common.aws.secrets_manager import get_key_from_secret_manager_credentials
from aws_lambda_powertools import Logger

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = Logger(child=True)


class GitClient:
    def __init__(self, base_url: str = None, repo: str = None, branch_name: str = None):
        """
        Uses Environment variables to create a github connection:

        Necessary Environment Variables:
            GITHUB_URL: The base url to the enterprise github, without Org or repo.
            SECRET_NAME: the location of the SecretsManager secret that contains the
                github api token.
            GIT_SECRET_KEY: the key the token is under within the above secret.
            REPO_NAME: the name of the repo to access for this lambda.
            BRANCH_NAME: the branch name to apply against. OPTIONAL: Can pass this
                value in the __init__
        """
        self._get_client(base_url)
        self._get_repo(repo)
        self._get_branch(branch_name)

    def _get_client(self, base_url: str):
        """
        Instantiates a github client

        Parameters:
            base_url: (str): The url for the enterprise server.
                this function automatically adds the '/api/v3'.
        """
        base_url = os.getenv("GITHUB_URL", base_url)

        if base_url[-1] == "/":
            base_url = base_url[:-1]
        try:
            access_token = get_key_from_secret_manager_credentials(
                os.getenv("SECRET_NAME"),
                os.getenv("GIT_SECRET_KEY"),
            )
            self.client = git.Github(
                base_url=f"{base_url}/api/v3", login_or_token=access_token, verify=False
            )
        except Exception as e:
            logger.exception("Unable to establish git connection")
            raise e

    def _get_repo(self, repo: str):
        """
        Retrieves the repo for actions.

        Raises:
            KeyError if REPO_NAME not found in env variables.
        """
        self.repo = self.client.get_repo(os.getenv("REPO_NAME", repo))

    def _get_branch(self, branch: str):
        """
        Retrieves the branch for actions.

        Prioritizes the env variable. If the env variable does not exist, uses the
        branch name provided in init.
        """

        self.branch = self.repo.get_branch(os.getenv("BRANCH_NAME", branch))

    def get_commit(self, commit_sha: str) -> Commit:
        """
        Returns
            [github.Commit.Commit] a particular commit by sha in the repo set at init.
        """

        return self.repo.get_commit(commit_sha)
