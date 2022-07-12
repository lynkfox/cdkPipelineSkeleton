import json
from dataclasses import dataclass


@dataclass
class LambdaVariables:
    """
    A parent class for Lambda Variables. Takes an event naturally, and is intended that __post_init__ in each
    child class will parse the event for its own functionality.

    Most child classes should mark all attributes as
        attribute: type = field(default=value, init=False)

    and have the `def __post_init__(self):` method in the child class set all the variables from the event


    Methods:
        as_dict() - Returns any variables of this dataclass as a dict, excluding those prefixed with `_`
            it has one optional parameter:
                include_none: bool - if True, will include any None attributes in the output, otherwise
                they will be ignored

        as_json() - Similar to as_dict(), it ignores event and and `_` prefixed variables. In addition, it
            outputs as a string that has been json.dumps() and takes two parameters:
                include_none: bool - If true, same as as_dict()
                best_naming: bool - defaults to True, and attempts to convert snake_case to camelCase.
                    setting this to false disables this and leaves the keys of the json field as snake_case

    """

    event: dict

    def as_dict(self, include_none: bool = False) -> dict:
        """
        Returns the data class as a dict, skipping any field that is currently none and ignoring any attribute
        that begins with '_'

        Ignores the event key automatically

        Parameters:
            include_none[bool][OPTIONAL]: Default to False, pass True if none values should be returned.

        Returns:
            [dict] of all attributes
        """

        return {
            key: value
            for key, value in self.__dict__.items()
            if (value is not None or include_none)
            and (key[0] != "_" and key != "event")
        }

    def as_json(self, include_none: bool = False, best_naming: bool = True) -> str:
        """
        similar to as_dict, but returns it already json.dumps and if best_naming is True (default)
        reformats attribute names to best practices (only top level attributes however).

        Parameters:
            include_none[bool][OPTIONAL]: Default to False, pass True if none values should be returned.
            best_naming[bool][OPTIONAL]: Default to True. cleans up names (remove underscores, capitalizes) - top level keys only (does not go into dicts)

        Returns:
            [str] json string.
        """

        output = self.as_dict(include_none=include_none)

        if best_naming:
            cleaned_output = {}
            for key, value in output.items():
                first_letter = key[0].lower()
                cleaned_key = (
                    key.lower().replace("_", " ").capitalize().replace(" ", "")
                )
                cleaned_key = first_letter + cleaned_key[1:]
                cleaned_output[cleaned_key] = value

            return json.dumps(cleaned_output)

        return json.dumps(output)
