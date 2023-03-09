import logging
import os
from typing import Any, Mapping

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()
logger = logging.getLogger(__name__)

try:
    username = os.getenv("MONGO_USERNAME")
    password = os.getenv("MONGO_PASSWORD")
    uri = os.getenv("MONGO_URI")
except Exception as e:
    logger.error(f"Error loading environment variables: {e}")


def get_database(db_name: str) -> Database[Mapping[str, Any] | Any]:
    """
    Simple wrapper function that gets the database from MongoDB
    :param db_name: name of the database to get
    :return: Database object
    """

    # throw an error if db_name is not a string or is empty
    if not isinstance(db_name, str) or not db_name:
        raise TypeError("db_name must be a non-empty string")

    connection_string = f"mongodb+srv://{username}:{password}@{uri}/?retryWrites=true"

    try:
        client = MongoClient(connection_string)
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise e

    # accessing the database will initialize it, but it will not be created until data is added
    return client[db_name]
