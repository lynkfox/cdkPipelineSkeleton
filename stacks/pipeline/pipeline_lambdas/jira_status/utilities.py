import os
from common.git_integration.git_client import GitClient
from github.Commit import Commit
from common.jira_integration.jira_client import JiraClient, JiraStatus
from datetime import datetime
from aws_lambda_powertools import Logger
from typing import List, Optional, Dict, Any
import re

logger = Logger(child=True)


class GitCommitHistory(GitClient):
    def __init__(self, commit_sha: str = None):
        super().__init__()
        self.commit = (
            self.repo.get_commit(sha=commit_sha) if commit_sha is not None else None
        )
        self.tag_name = os.getenv("TAG_VALUE", "Tagged")

        return

    def update_jira(self, commit_sha: Optional[str] = None) -> Dict[str, Any]:
        """
        Updates JIRA cards found in commit messages to DONE status if Prod or IN REVIEW
        if dev.

        Parameters:
            commit_sha: Optional[str] - an optional sha to find commits leading UP TO.

        Returns:
            List of card numbers that were updated.

        """
        commit_history = self._get_all_commits_since_last_deployment(commit_sha)

        self.jira_client = MassJiraUpdate(card_numbers)
        card_numbers = [
            self._parse_for_issue_number(commit, self.jira_client.project)
            for commit in commit_history
        ]

        self.jira_client.update_status(card_numbers)

        return {
            "allCards": list(filter(None, card_numbers)),
            "notFoundCards": self.jira_client.cards_not_found,
            "errorCards": self.jira_client.cards_error_out,
            "successfulCards": self.jira_client.cards_updated,
        }

    def _get_all_commits_since_last_deployment(self, commit_sha: str = None):
        """
        Checks over the git history since the last tag for a deployment, retrieving all
        commits

        Parameters:
            commit_sha: the sha to reference from. If none, will use self.tag_name
                to find the tag's sha instead.
        """

        if commit_sha is None:
            reference_sha = self.repo.get_git_ref(ref=self.tag_name).object.sha

        else:
            reference_sha = commit_sha

        last_deployment_commit_time = self.repo.get_commit(
            sha=reference_sha
        ).commit.author.date
        # Python requests have an interesting habit of coming back as datetime.datetime
        # objects instead of as a string but its hard to tell this when looking at an
        # output, cause it gets automatically stringified.
        #
        # which would be fine except get_commits(since) requires a string...
        if isinstance(last_deployment_commit_time, str):
            last_deployment_commit_time = datetime.strptime(
                last_deployment_commit_time, "%Y-%m-%d %H:%M:%S"
            )

        if last_deployment_commit_time is None:
            logger.warning(f"No Commit found with tag {self.tag_name}")

        return (
            self.repo.get_commits(since=last_deployment_commit_time)
            if last_deployment_commit_time is not None
            else None
        )

    def _parse_for_issue_number(self, commit: Commit, project_id: str) -> Optional[str]:
        """
        Parses commits for a project ID and card number in the commit message, and returns
        all found issue numbers.

        Parameter:
            commit: [github.Commit.Commit] single commit object from get_commits pagination
            project_id: [str] - the project id to search for

        Returns:
            card_number: [str] the card value or None

        Expects:
            the card number to be some variety of: ABCD-1234 | ABCD 1234 | ABCD - 1234
            and ignores case
        """

        return re.search(
            f"({project_id.lower()})" + "(\s{0,1}-{0,1}\s{0,1})(\d{4})",
            commit.commit.message,
            re.IGNORECASE,
        )


class MassJiraUpdate(JiraClient):
    def __init__(self, jira_url: str = None, jira_project: str = None) -> None:
        super().__init__(jira_url, jira_project)
        self.cards_not_found = []
        self.cards_error_out = []
        self.cards_updated = []

    def update_status(self, card_numbers: List[str]):
        self.card_numbers = card_numbers
        self._update_all_to_status(JiraStatus[os.getenv("UPDATE_TO_STATUS", "REVIEW")])

    def _update_all_to_status(self, status: JiraStatus):
        """
        Loops over the card numbers provided and updates them all to the jira status
        provided

        Parameters:
            status: [JiraStatus] - a status Enum
        """

        for issue in self.card_numbers:
            try:
                if issue is None:
                    continue
                self.update_card_status(issue, status)

                self.card_updated.append(issue)
                logger.info(
                    "Cards Updated",
                    extra={
                        "jiraIssueNumbers": self.card_numbers,
                        "updateToStatus": str(status),
                    },
                )

            except ValueError as e:
                self.cards_not_found.append(issue)
                continue

            except Exception as e:
                self.cards_error_out.append((issue, str(e)))
                continue
