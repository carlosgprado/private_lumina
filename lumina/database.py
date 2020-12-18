from pymongo import MongoClient

import os, json
from base64 import b64encode, b64decode

class LuminaDatabase(object):
    def __init__(self, logger, db_name="test"):
        self.logger = logger
        self.client = None
        self.db = None
        self.collection = None

        self.load(db_name)


    def load(self, db_name):
        self.client = MongoClient('mongodb://mongoadmin:secret@localhost:27017/')

        try:
            self.db = self.client[db_name]
            self.collection = self.db['lumina_data']
        except Exception as e:
            self.logger.exception(e)
            self.client.close()
            raise

    def close(self, save=False):
        self.client.close()

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
            new_entry = {
                "sig": signature,
                "metadata": list(),
                "popularity" : 0
            }

            # Actually insert this data into the collection :)
            try:
                self.collection.insert_one(new_entry)
                new_sig = True
            except Exception as e:
                self.logger.error(e)

        else:
            # Existing entry. Update it.
            db_entry["metadata"].append(metadata)
            db_entry["popularity"] += 1
            self.collection.update(
                    {"sig": signature},
                    {"$set": {
                        "metadata": db_entry["metadata"],
                        "popularity": db_entry["popularity"]
                        }})

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
            _metadata_list = db_entry["metadata"]
            if _metadata_list:
                metadata = _metadata_list[-1]
            else:
                return None

            # Decode signature (take that last match for a result)
            _metadata = {
                "func_name"         : metadata["func_name"],
                "func_size"         : metadata["func_size"],
                "serialized_data"   : b64decode(metadata["serialized_data"]),
            }

            result = {
                "metadata"   : _metadata,
                "popularity" : db_entry["popularity"]
            }

            return result

        return None
