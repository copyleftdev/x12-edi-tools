from typing import List, Dict, Any, Union
from dataclasses import dataclass
import json
import logging
from abc import ABC, abstractmethod

@dataclass
class X12Segment:
    segment_id: str
    elements: List[str]

class DatabaseConnector(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def execute(self, query: str, params: tuple = ()):
        pass

    @abstractmethod
    def fetch_all(self, query: str, params: tuple = ()):
        pass

    @abstractmethod
    def get_last_insert_id(self) -> int:
        pass

    @abstractmethod
    def get_placeholder(self) -> str:
        pass

class X12DatabaseIntegratorError(Exception):
    """Custom exception for X12DatabaseIntegrator errors."""

class X12DatabaseIntegrator:
    """
    A robust, database-agnostic integrator for X12 data.
    
    This class provides methods to store, retrieve, and query X12 data in a database,
    regardless of the specific database system being used.
    """
    
    def __init__(self, db_connector: DatabaseConnector):
        """
        Initialize the X12DatabaseIntegrator.
        
        Args:
            db_connector (DatabaseConnector): A database connector object.
        """
        self.db = db_connector
        self.logger = self._setup_logger()
        self.placeholder = self.db.get_placeholder()

    def setup_database(self):
        """Set up the necessary tables in the database."""
        try:
            self.db.connect()
            self.db.execute(f'''
                CREATE TABLE IF NOT EXISTS x12_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_type TEXT,
                    sender_id TEXT,
                    receiver_id TEXT,
                    transaction_date TEXT,
                    content TEXT
                )
            ''')
            self.db.execute(f'''
                CREATE TABLE IF NOT EXISTS x12_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER,
                    segment_id TEXT,
                    elements TEXT,
                    FOREIGN KEY (transaction_id) REFERENCES x12_transactions (id)
                )
            ''')
        except Exception as e:
            raise X12DatabaseIntegratorError(f"Failed to set up database: {str(e)}")
        finally:
            self.db.disconnect()

    def store_transaction(self, transaction_type: str, sender_id: str, receiver_id: str, 
                          transaction_date: str, content: str, segments: List[X12Segment]):
        """
        Store an X12 transaction and its segments in the database.
        
        Args:
            transaction_type (str): The type of X12 transaction (e.g., "837", "835").
            sender_id (str): The sender's identifier.
            receiver_id (str): The receiver's identifier.
            transaction_date (str): The date of the transaction.
            content (str): The full X12 transaction content.
            segments (List[X12Segment]): List of X12Segment objects.
        
        Raises:
            X12DatabaseIntegratorError: If storing the transaction fails.
        """
        try:
            self.db.connect()
            self.db.execute(f'''
                INSERT INTO x12_transactions (transaction_type, sender_id, receiver_id, transaction_date, content)
                VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
            ''', (transaction_type, sender_id, receiver_id, transaction_date, content))
            
            transaction_id = self.db.get_last_insert_id()
            
            for segment in segments:
                self.db.execute(f'''
                    INSERT INTO x12_segments (transaction_id, segment_id, elements)
                    VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder})
                ''', (transaction_id, segment.segment_id, json.dumps(segment.elements)))
            
            self.logger.info(f"Stored transaction {transaction_id} of type {transaction_type}")
        except Exception as e:
            raise X12DatabaseIntegratorError(f"Failed to store transaction: {str(e)}")
        finally:
            self.db.disconnect()

    def retrieve_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """
        Retrieve an X12 transaction and its segments from the database.
        
        Args:
            transaction_id (int): The ID of the transaction to retrieve.
        
        Returns:
            Dict[str, Any]: A dictionary containing the transaction details and segments.
        
        Raises:
            X12DatabaseIntegratorError: If retrieving the transaction fails.
        """
        try:
            self.db.connect()
            transaction = self.db.fetch_all(f'''
                SELECT * FROM x12_transactions WHERE id = {self.placeholder}
            ''', (transaction_id,))
            
            if not transaction:
                raise X12DatabaseIntegratorError(f"Transaction {transaction_id} not found")
            
            segments = self.db.fetch_all(f'''
                SELECT segment_id, elements FROM x12_segments WHERE transaction_id = {self.placeholder}
            ''', (transaction_id,))
            
            return {
                "transaction": transaction[0],
                "segments": [{"segment_id": seg[0], "elements": json.loads(seg[1])} for seg in segments]
            }
        except Exception as e:
            raise X12DatabaseIntegratorError(f"Failed to retrieve transaction: {str(e)}")
        finally:
            self.db.disconnect()

    def query_transactions(self, **kwargs) -> List[Dict[str, Any]]:
        """
        Query X12 transactions based on given criteria.
        
        Args:
            **kwargs: Keyword arguments for filtering transactions.
        
        Returns:
            List[Dict[str, Any]]: A list of matching transactions.
        
        Raises:
            X12DatabaseIntegratorError: If querying transactions fails.
        """
        try:
            self.db.connect()
            query = "SELECT * FROM x12_transactions WHERE 1=1"
            params = []
            for key, value in kwargs.items():
                query += f" AND {key} = {self.placeholder}"
                params.append(value)
            
            transactions = self.db.fetch_all(query, tuple(params))
            return [dict(zip([column[0] for column in self.db.cursor.description], t)) for t in transactions]
        except Exception as e:
            raise X12DatabaseIntegratorError(f"Failed to query transactions: {str(e)}")
        finally:
            self.db.disconnect()

    def _setup_logger(self) -> logging.Logger:
        """Set up a logger for the X12DatabaseIntegrator."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def __repr__(self) -> str:
        """Provide a string representation of the X12DatabaseIntegrator."""
        return f"X12DatabaseIntegrator(db={self.db})"