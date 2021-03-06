"""
Abstract base class for any enrichment class

"""
from abc import ABC, abstractmethod


class Enricher(ABC):

    @classmethod
    @abstractmethod
    def enriches(cls, app_name, catalog_name, entity_name):
        """
        Tells wether this class enriches the given catalog - entity
        :param catalog_name:
        :param entity_name:
        :return:
        """
        pass

    def __init__(self, app_name, catalogue_name, entity_name, methods):
        """
        Given the methods and entity name, the enrich_entity method is set

        :param methods:
        :param entity_name:
        """
        self.app_name = app_name
        self.catalogue_name = catalogue_name
        self.entity_name = entity_name
        self._enrich_entity = methods.get(entity_name)

    def enrich(self, entity):
        """
        Enrich a single entity

        :param entity:
        :return:
        """
        if self._enrich_entity:
            self._enrich_entity(entity)

    def cleanup(self):
        """
        Cleanup an enricher e.g. delete temporary files

        :return:
        """
        pass
