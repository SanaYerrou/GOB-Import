""" Validator

Basic validation logic

The first version implements only the most basic validation logic
In order to prepare a more generic validation approach the validation has been set up by means of regular expressions.

"""
from enum import Enum
import re

from gobcore.exceptions import GOBException
from gobcore.model import GOBModel
from gobcore.model.metadata import FIELD
from gobcore.logging.logger import logger


# Log message formats
MISSING_ATTR_FMT = "{attr} missing in entity: {entity}"
QA_CHECK_FAILURE_FMT = "{msg}. Value was: {value}"


NL_X_MIN = 110000
NL_X_MAX = 136000
NL_Y_MIN = 474000
NL_Y_MAX = 502000


class QA(Enum):
    FATAL = "fatal"
    WARNING = "warning"
    INFO = "info"


ENTITY_CHECKS = {
    "test_entity": {},
    "meetbouten": {
        "identificatie": [
            {
                "pattern": "^\d{8}$",
                "msg": "identificatie should consist of 8 numeric characters",
                "type": QA.FATAL,
            },
        ],
        "status_id": [
            {
                "pattern": "^[1,2,3]$",
                "msg": "Statusid should be one of [1,2,3].",
                "type": QA.WARNING,
            },
        ],
        "windrichting": [
            {
                "pattern": "^(N|NO|O|ZO|Z|ZW|W|NW)$",
                "msg": "Windrichting should be one of [N,NO,O,ZO,Z,ZW,W,NW]",
                "allow_null": True,
                "type": QA.WARNING,
            }
        ],
        "publiceerbaar": [
            {
                "pattern": "^[1,0]$",
                "msg": "Publiceerbaar should be one of [1,0]",
                "allow_null": True,
                "type": QA.WARNING,
            },
        ],
    },
    "metingen": {
        "identificatie": [
            {
                "pattern": "^\d+$",
                "msg": "identificatie should be a valid positive integer",
                "type": QA.FATAL,
            },
        ],
        "hoort_bij_meetbout": [
            {
                "pattern": "^\d{8}$",
                "msg": "identificatie should consist of 8 numeric characters",
                "type": QA.FATAL,
            },
        ],
        "publiceerbaar": [
            {
                "pattern": "^[1,0]$",
                "msg": "Publiceerbaar should be one of [1,0]",
                "allow_null": True,
                "type": QA.WARNING,
            },
        ],
    },
    "referentiepunten": {
        "publiceerbaar": [
            {
                "pattern": "^[J,N]$",
                "msg": "Publiceerbaar should be one of [J,N]",
                "allow_null": True,
                "type": QA.FATAL,
            },
        ],
    },
    "rollagen": {
        "name": [
            {
                "pattern": "(.*)/([a-zA-Z]{2}\d{1,2}).(.*)",
                "msg": "File name should be in the format AAn(n)",
                "type": QA.FATAL,
            },
        ],
    },
    "peilmerken": {
        "identificatie": [
            {
                "pattern": "^\d{8}$",
                "msg": "identificatie should of 8 numeric characters",
                "type": QA.FATAL,
            },
        ],
        "hoogte_tov_nap": [
            {
                "between": [-6, 15],
                "msg": "hoogte_tov_nap should be a numeric value between -6 and 15",
                "type": QA.WARNING,
            },
        ],
        "geometrie": [
            {
                "geometry": {
                    'x': {
                        'min': NL_X_MIN,
                        'max': NL_X_MAX,
                    },
                    'y': {
                        'min': NL_Y_MIN,
                        'max': NL_Y_MAX,
                    }
                },
                "msg": f"geometrie coordinates should be between {NL_X_MIN}-{NL_X_MAX} and {NL_Y_MIN}-{NL_Y_MAX}",
                "type": QA.FATAL,
            },
        ],
        "publiceerbaar": [
            {
                "pattern": "^[JN]{1}$",
                "msg": "publiceerbaar should be J or N",
                "allow_null": True,
                "type": QA.FATAL,
            },
        ]
    },
    "bouwblokken": {
        "source_id": [
            {
                "source_app": "DGDialog",
                "pattern": "^{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}}$",
                "msg": "source_id should be a 4-2-2-2-6 bytes hexidecimal value",
                "type": QA.WARNING
            }
        ],
        "code": [
            {
                "pattern": "^[a-zA-Z]{2}\d{2}$",
                "msg": "code should be 2 letters and 2 numbers",
                "type": QA.FATAL
            }
        ],
    },
    "buurten": {
        "geometrie": [
            {
                "geometry": {
                    'x': {
                        'min': NL_X_MIN,
                        'max': NL_X_MAX,
                    },
                    'y': {
                        'min': NL_Y_MIN,
                        'max': NL_Y_MAX,
                    }
                },
                "msg": f"geometrie coordinates should be between {NL_X_MIN}-{NL_X_MAX} and {NL_Y_MIN}-{NL_Y_MAX}",
                "type": QA.FATAL,
            },
        ],
        "naam": [
            {
                "pattern": "^.+$",
                "msg": "naam should be filled",
                "type": QA.WARNING
            }
        ],
    },
    "wijken": {
        "code": [
            {
                "pattern": "^[a-zA-Z]{1}\d{2}$",
                "msg": "code should be 1 letter and 2 numbers",
                "type": QA.FATAL
            }
        ],
        "documentnummer": [
            {
                "pattern": "^.+$",
                "msg": "documentnummer should be filled",
                "type": QA.WARNING,
            },
        ],
    },
    "ggpgebieden": {
        "GGP_NAAM": [
            {
                "pattern": "^[^0-9]+$",
                "msg": "naam should be filled and not contain numbers",
                "type": QA.WARNING,
            },
        ],
    },
    "ggwgebieden": {
        "GGW_NAAM": [
            {
                "pattern": "^[^0-9]+$",
                "msg": "naam should be filled and not contain numbers",
                "type": QA.WARNING,
            },
        ],
    },
    "stadsdelen": {
        "naam": [
            {
                "pattern": "^[^0-9]+$",
                "msg": "naam should be filled and not contain numbers",
                "type": QA.WARNING,
            },
        ],
    }
}


class Validator:

    def __init__(self, source_app, entity_name, source_id, input_spec):
        self.source_app = source_app
        self.entity_name = entity_name
        self.source_id = source_id
        self.input_spec = input_spec

        checks = ENTITY_CHECKS.get(entity_name, {})
        self.collection_qa = {f"num_invalid_{attr}": 0 for attr in checks.keys()}
        self.fatal = False

        self.primary_keys = set()
        self.duplicates = set()

    def result(self):
        if self.fatal:
            raise GOBException(
                f"Quality assurance failed for {self.entity_name}"
            )

        if self.duplicates:
            raise GOBException(f"Duplicate primary key(s) found in source: "
                               f"[{', '.join([str(dup) for dup in self.duplicates])}]")

        self._log(type=QA.INFO,
                  id=None,
                  msg=f"Quality assurance passed",
                  data=self.collection_qa)

    def validate(self, entity):
        """
        Validate a single entity

        :param self:
        :return:
        """
        # Validate uniqueness of primary key
        self._validate_primary_key(entity)

        # Run quality checks on the collection and individual entities
        self._validate_quality(entity)

    def _log(self, type, id, msg, data):
        extra_info = {
            "id": id,
            "data": data
        }
        if type == QA.FATAL:
            logger.error(msg, extra_info)
        if type == QA.WARNING:
            logger.warning(msg, extra_info)
        if type == QA.INFO:
            logger.info(msg, extra_info)

    def _validate_primary_key(self, entity):
        """
        Validate a primary key, this should be unique for source_id + seqnr if the collection has states

        :param entity:
        :return:
        """

        entity_has_states = GOBModel().has_states(self.input_spec['catalogue'], self.input_spec['entity'])

        if entity_has_states:
            # Volgnummer could be a different field in the source entity than FIELD.SEQNR
            try:
                seqnr_field = self.input_spec['gob_mapping'][FIELD.SEQNR]['source_mapping']
            except KeyError:
                seqnr_field = FIELD.SEQNR

        id = f"{entity[self.source_id]}.{entity[seqnr_field]}" if entity_has_states else entity[self.source_id]
        if id is not None:
            # Only add ids that are not None, None id's can occur for imports of collections without ids
            if id not in self.primary_keys:
                self.primary_keys.add(id)
            else:
                self.duplicates.add(id)

    def _validate_entity(self, entity):
        """
        Validate a single entity.

        Fails on any fatal validation check
        Warns on any warning validation check
        All info validation checks are counted

        :param entity_name: the entity name
        :param entity: a single entity
        :return: Result of the qa checks
        """
        qa_checks = ENTITY_CHECKS.get(self.entity_name, {})

        invalid_attrs = set()

        for attr, entity_checks in qa_checks.items():
            for check in entity_checks:
                if check.get("source_app", self.source_app) != self.source_app:
                    # Checks can be made app specific by setting the source_app attribute
                    continue
                # Check if the attribute is available
                if not self._attr_check(check, attr, entity):
                    # Add the attribute to the set of non-valid attributes for count
                    invalid_attrs.add(attr)
                    continue

                if not self._qa_check(check, attr, entity):
                    # Add the attribute to the set of non-valid attributes for count
                    invalid_attrs.add(attr)

        return invalid_attrs

    def _attr_check(self, check, attr, entity):
        type = check["type"]
        # Check if attr is available in entity
        if attr not in entity:
            # If a fatal check has failed, mark the validation as fatal
            if type == QA.FATAL:
                self.fatal = True

            # Log the missing attribute, with the correct level
            self._log(type=type,
                      id="Missing attribute",
                      msg=MISSING_ATTR_FMT.format(attr=attr, entity=entity[self.source_id]),
                      data={self.source_id: entity[self.source_id], "missing_attr": attr})

            return False

        return True

    # TODO: fix too complex
    def _qa_check(self, check, attr, entity):   # noqa: C901
        msg = check["msg"]
        type = check["type"]
        value = entity[attr]
        if 'pattern' in check:
            is_correct = self._regex_check(check, value)
        elif 'between' in check:
            is_correct = self._between_check(check['between'], value)
        elif 'geometry' in check:
            is_correct = self._geometry_check(check['geometry'], value)

        # If the value doesn't pass the qa check, handle the correct way
        if not is_correct:
            # If a fatal check has failed, mark the validation as fatal
            if type == QA.FATAL:
                self.fatal = True

            # Log the missing attribute, with the correct level
            self._log(type=type,
                      id=msg,
                      msg=QA_CHECK_FAILURE_FMT.format(msg=msg, value=value),
                      data={self.source_id: entity[self.source_id], "value": value})

            return False

        return True

    def _regex_check(self, check, value):
        # Check if Null values are allowed
        allow_null = check.get('allow_null')
        if allow_null and value is None:
            return True
        elif not allow_null and value is None:
            return False
        return re.compile(check['pattern']).match(str(value))

    def _between_check(self, between, value):
        return value >= between[0] and value <= between[1] if value is not None else False

    def _geometry_check(self, between, value):
        coords = re.findall('([0-9]+\.[0-9]+)', value)
        # Loop through all coords and check if they fill within the supplied range
        # Even coords are x values, uneven are y values
        coord_types = ['x', 'y']
        for count, coord in enumerate(coords):
            # Get the coord type
            coord_type = coord_types[count % 2]
            # If the coord is outside of the boundaries, retun false
            if not(between[coord_type]['min'] <= float(coord) <= between[coord_type]['max']):
                return False
        return True

    def _validate_quality(self, entity):
        """
        Validate an entity.

        Fails on any fatal validation check
        Warns on any warning validation check
        All info validation checks are counted

        :param entity_name: the entity name
        :param entity: a single entity
        :param source_id: the column defining the unique identifier
        :return: Result of the qa checks, and a boolean if fatal errors have been found
        """
        # Validate on individual entities
        invalid_attrs = self._validate_entity(entity)
        for attr in invalid_attrs:
            self.collection_qa[f"num_invalid_{attr}"] += 1
