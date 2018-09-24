"""ImportClient class

An ImportClient is instantiated using a configuration and dataset definition.
The configuration is shared between import clients and contains for instance the message broker to
publish the results
The dataset is specific for each import client and tells for instance which fields should be extracted

The current implementation assumes csv-file based imports

Todo: improve type conversion
    e.g. for bools the true and false values are hardcoded.
    N = False, else is True, but this can vary per import
"""

import datetime

from gobcore.events.import_message import MessageMetaData, ImportMessage
from gobcore.message_broker import publish

from gobimportclient.connector import connect_to_file
from gobimportclient.converter import convert_from_file


class ImportClient:
    """Main class for an import client

    This class serves as the main client for which the import can be configured in a dataset.json

    """
    def __init__(self, dataset):
        self._dataset = dataset
        self.source = self._dataset['source']

        self._data = None       # Holds the data in imput format
        self._gob_data = None   # Holds the imported data in GOB format

    def connect(self):
        """The first step of every import is a technical step. A connection need to be setup to
        connect to a database, filesystem, API, ...

        :return:
        """
        if self.source['type'] == "file":
            self._data = connect_to_file(config=self.source['config'])
        else:
            raise NotImplementedError

    def read(self):
        """Read the data from the data source

        :return:
        """
        if self.source['type'] == "file":
            #  No action required here, data is read by pandas in self._data
            pass
        else:
            raise NotImplementedError

    def convert(self):
        """Convert the input data to GOB format

        Todo: quality check (where should that be implemented) make sure no double id's are imported.

        :return:
        """
        if self.source['type'] == "file":
            self._gob_data = convert_from_file(self._data, dataset=self._dataset)
        else:
            raise NotImplementedError

    def publish(self):
        """The result of the import needs to be published.

        Publication includes a header, summary and results
        The header is for identification purposes
        The summary is for the interpretation of the results. Was the import successful, what er the metrics, etc
        The results is the imported data in GOB format

        :return:
        """
        metadata = MessageMetaData(
            source=self._dataset['source']['name'],
            id_column=self._dataset['entity_id'],
            entity=self._dataset['entity'],
            version=self._dataset['version'],
            model=self._dataset['gob_model'],
            timestamp=datetime.datetime.now().isoformat()
        )

        import_message = ImportMessage.create_import_message(metadata.as_header, None, self._gob_data)

        publish("gob.workflow.proposal", "fullimport.proposal", import_message)