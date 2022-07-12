from dataclasses import dataclass


@dataclass(frozen=True)
class AttributeName:
    """
    These constants are the names of attributes found within DynamoDB entries. Use of
    these class variables reduces mistakes in spelling and typos.

    NOTE! Changing one of these values WILL NOT change the attribute on existing entries
    in an existing dynamo. Retroactive changes like that will have to be handled through
    a script of some kind to update the table.

    Adding new attributes however, as soon as they are used in the code and sent to
    dynamo, will add the new attribute for that item just fine - However it will not
    exist for older items!
    """

    TIME_TO_LIVE = "time_to_live"


@dataclass(frozen=True)
class KeyName:
    """
    Partition and Sort Key attribute names
    """

    # It is HIGHLY recommended to carefully consider your Dynamodb access patterns
    # It is HIGHLY recommended not to change these values, and instead work with prefix's
    # to their value to define specific document types. Remember: Dynamo is NOT a
    # relational database!
    PARTITION = "pk"
    SORT = "sk"
