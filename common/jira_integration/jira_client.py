import jira
import os
from aws_lambda_powertools import Logger
from common.aws.secrets_manager import get_key_from_secret_manager_credentials
from enum import Enum
from typing import Optional

logger = Logger(child=True)


class JiraStatus(Enum):
    """
    Enum class for Jira Status levels.

    Each Enum member name is a given status, and its value is the corresponding Jira
    Status ID for use with the api.

    Jira Status are represented as an int ID in the API, but these are not set in stone.
    This class will need to be updated for each project or some kind of mapping will
    need to be added to make sure they correspond to the correct values.

    You can get the Jira Status IDs in one of two ways:

    1) Assuming you have Jira Admin rights, then you can access Jira Administration >
        Issues > Statuses.  You can then hover the "Edit" option under the ACTION column
        to see each status's ID (The link should show up at the bottom left of your
        screen).

    2) Issue the following REST API call via a browser tab -
        https://<based Jira URL address>/rest/api/2/status.  It will give you a listing
        of all WF statuses in your system with its ID.
    """

    # NOTE: Your project may require these members to be different. Change them as you
    # see fit, but do note that more jira status is not necessarily a good thing. Many
    # times you only need these statuses and any more is a complication. The statuses
    # below cover every major stage of a card, and when utilized with good automation
    # there will never need to be more.

    # Jira Status are represented by a status ID in Jira, that is assigned depending on
    # some amount of factors. Probably current # of statuses in the system or something.
    # As such the values for these Enums correspond with the

    BACKLOG = 1
    """
    BACKLOG status is for cards that are not yet started; they may or may not still be
    gathering requirements and being groomed.
    """

    ASSIGNED = 2
    """
    ASSIGNED status is for any card that has been picked up by a dev - either on their
    own or assigned during Sprint Planning.  This status covers all dev work - from
    finalizing any analysis to testing. IF cards are small of scope and properly built
    there should be no need for another status that basically corresponds to "Dev is
    working on this"

    Automation Uses: Set card # to this status when a branch is created with corresponding
        card number. Set card to this status when rejected by Review
    """

    REVIEW = 3
    """
    REVIEW status is for any card that is ready to go to prod. It has Passed all the
    tests and been merged into the Dev Branch, OR the Main branch but the pipeline
    corresponding to its card # has not yet passed the clean up phase of assigning cards
    to DONE.

    Automation Uses: Set card # to this status when a branch with the same # is merged
        into dev branch - OR if no Dev branch and maintaining a one branch strategy when
        a card reaches the Review stage of a pipeline and is waiting on Business Partner
        review.
    """

    DONE = 4
    """
    DONE status is ONLY for cards that have passed all stages of the pipeline and
    successfully deployed to production. This status should ONLY be controlled and set
    by the Pipeline, and only as the final step once all other processes have successfully
    completed. Manual setting of this status should be blocked.

    Automation Uses: Once the pipeline to deploy to Production is fully complete, all
    tests have passed, then any commit with this card# in it should be set to DONE and
    this should ONLY be set by automation - never by hand.
    """

    ANALYSIS = 5
    """
    ANALYSIS Status is for Spike Cards. This can be replaced with BACKLOG in most
    situations as Analysis of a given card should be done as part of its card grooming.

    Automation Uses: Any card of a Spike Variety or with a specific tag could be set
        to this status.
    """

    NON_PROD_DONE = 6
    """
    NON_PROD_DONE status is for any card that will not be entering Prod. This can be for
    cards that have been rejected as not needed or no longer going to happen. This can
    be for Spike or Info Tracking cards that do not enter prod, or for Tools/utilities
    that are built but never enter the Prod deployment pipeline.

    Automation Uses: For any card that needs to be set as complete but isn't a part of a
        prod deployment.
    """


class JiraClient:
    """
    Base jira class for setting up and utilizing Jira integration clients

    Uses Environment Variables to determine what it needs, including:

        JIRA_SECRET_KEY - the key for the map in the SecretManager that contains the
            authentication token
        JIRA_SECRET_USER - The key for the map in the SecretManager that contains the
            user name for Jira
        JIRA_PROJECT - The project identifier from Jira
        JIRA_SERVER - the URL of the JiraServer
    """

    def __init__(self, jira_url: str = None, jira_project: str = None) -> None:
        self.project = os.getenv("JIRA_PROJECT", jira_project)
        self._get_jira_client(os.getenv("JIRA_URL", jira_url))
        pass

    def update_card_status(
        self, card: str, status: JiraStatus, message: Optional[str] = None
    ) -> bool:
        """
        Updates a provided issue to the provided status.

        Parameters:
            issue: [str] - either the full issue (ABCD-1234) or just the number (1234)
                as a string. If just the number will used the project set at init.
            status: [JiraStatus] - the status to set the jira issue too.
            message: [Optional[str]] - a custom message for the automation to add to the
                card on successful status update. If None, then a default message is
                added.

        Returns:
            [boolean] True if successful

        Raises:
            [ValueError] Jira Issue not found.
            [jira.JiraError] Any complication in moving a Jira Issue to the new status
        """
        logger.append_keys(
            jiraCardNumber=card, jiraProject=self.project, newStatus=str(status)
        )

        if card is None or card.strip() == "":
            logger.error("No Card number provided to update.")

        try:
            issue = self._get_card(issue=card)
        except jira.JIRAError as e:
            logger.exception(f"Could not find jira issue of {card}.")
            raise ValueError(f"JiraIssueNotFound-{card}")

        logger.append_keys(oldStatus=issue.fields.status)

        if issue.fields.status == status.value:
            logger.warning("Issue already in provided status")
            return False

        self.client.transition_issue(issue, status.value)

        if message == None:
            message = f"Card moved to Status [{status.name}] by automation"

        self.client.add_comment(issue, message)
        logger.info("Card Status updated")

        logger.remove_keys(["jiraCardNumber", "jiraProject", "newStatus", "oldStatus"])

        return True

    def _get_jira_client(self, jira_server_url: str):
        """
        Creates a client for Jira API interactions
        """
        try:
            auth_token = get_key_from_secret_manager_credentials(
                os.environ["SECRET_NAME"], os.environ["JIRA_SECRET_KEY"]
            )

            username = get_key_from_secret_manager_credentials(
                os.environ["SECRET_NAME"], os.environ["JIRA_SECRET_USER"]
            )

            self.client = jira.JIRA(
                server=jira_server_url, basic_auth=(username, auth_token)
            )
        except Exception as e:
            logger.exception("Unable to establish git connection")
            raise e

    def _get_card(self, issue: str) -> jira.JIRA.issue:
        """
        Retrieves a given issue by the card number - just the number - relying on the
        set project identifier.

        Parameters:
            issue: [str] - the number of the issue to retrieve. If
                it only contains 4 characters and no project identifier it will use the
                project id set at client creation.

        Returns
            [jira.JIRA.issue] - the Jira Issue to be manipulated
        """

        if len(issue) == 4:
            issue = f"{self.project}-{issue}"

        return self.client.issue(issue)
