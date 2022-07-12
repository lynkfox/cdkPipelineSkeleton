import base64
import json

import boto3


def get_credentials_from_secret_manager(
    secret_name: str, region_name: str = "us-east-1"
) -> str:
    """
    Helper function for accessing secrets from our SecretsManager.

    Parameters:
        secret_name(String): The key of the Secret.
        region_name(String): [Optional] - such as us-east-1 (defaults to this).

    Returns:
        (String): The secret string or decoded secret binary.

    Raises
        (ClientError): Boto3/AWS issues - Note if "SecretNotFound" is returned, be
        aware that this usually means that permissions are not properly set up for
        the calling system to access the Secrets
        ()
    """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    secret_value_response = client.get_secret_value(SecretId=secret_name)

    if "SecretString" in secret_value_response:
        return secret_value_response["SecretString"]
    else:
        return base64.b64decode(secret_value_response["SecretBinary"]).decode("utf8")


def get_key_from_secret_manager_credentials(
    secret_name: str, key_name: str, region_name: str = "us-east-1"
) -> str:
    """
    Gets the credentials from the secret manager and pulls a specific key from them.

    Args:
        secret_name (str): The name of the secret to get.
        key_name (str): The key to pull from the credentials JSON.
        region_name (str): The region to get the secret from.

    Returns:
        (str): The string pulled from the credentials JSON.

    Exceptions:
        (KeyError): Raised if key not in secret given.
    """
    credentials = get_credentials_from_secret_manager(secret_name, region_name)
    credentials_dict = json.loads(credentials)
    return credentials_dict[key_name]
