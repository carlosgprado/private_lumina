from pymongo import MongoClient

import os, json
from base64 import b64encode, b64decode

class LuminaDatabase(object):
    def __init__(self, logger, db_name='test'):
        self.logger = logger
        self.client = None
        self.db = None
        self.collection = None

        self.load(db_name)


    def load(self, db_name):
        self.client = MongoClient()

        try:
            self.db = self.client[db_name]
            self.collection = self.db['lumina_data']
        except Exception as e:
            self.logger.exception(e)
            self.client.close()
            raise

    def close(self, save=False):
        self.client.close()
        self.db.close()

    def push(self, info):
        """Return True on new insertion, else False"""

        # Signature and metadata contains non string data that need to be encoded:
        sig_version = info.signature.version
        signature = b64encode(info.signature.signature).decode("ascii")

        metadata = {
            "func_name"         : info.metadata.func_name,
            "func_size"         : info.metadata.func_size,
            "serialized_data"   : b64encode(info.metadata.serialized_data).decode("ascii"),
        }

        if sig_version != 1:
            self.logger.warning("Signature version {sig_version} not supported. Results might be inconsistent")

        # Insert into database
        new_sig = False
        db_entry = self.collection.find_one({"sig": signature})

        if db_entry is None:
            # The entry does NOT exist in the collection. Create a new one.
            # TODO: Collision/merge not implemented yet. Just keep every push queries.
            db_entry = {
                "sig": signature,
                "metadata": list(),
                "popularity" : 0
            }

            new_sig = True
        else:
            # Existing entry. Update it.
            db_entry["metadata"].append(metadata)
            db_entry["popularity"] += 1

        # Actually insert this data into the collection :)
        self.collection.insert_one(db_entry)

        return new_sig


    def pull(self, signature):
        """Return function metadata or None if not found"""

        sig_version = signature.version
        signature = b64encode(signature.signature).decode("ascii")

        if sig_version != 1:
            self.logger.warning("Signature version {sig_version} not supported. Results might be inconsistent")

        # Query database
        db_entry = self.collection.find_one({"sig": signature})

        if db_entry:
            # Take last signature (arbitrary choice)
            metadata = db_entry["metadata"][-1]

            # Decode signature (take that last match for a result)
            metadata = {
                "func_name"         : metadata["func_name"],
                "func_size"         : metadata["func_size"],
                "serialized_data"   : b64decode(metadata["serialized_data"]),
            }

            result = {
                "metadata"   : metadata,
                "popularity" : db_entry["popularity"]
            }

            return result

        return None
