from contextlib import contextmanager
from typing import Any, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from ....shared.config import config
from ....shared.logging.logger import logger
from .exceptions import DatabaseConnectionError, DatabaseQueryError, DatabaseTransactionError
from .models import Base

# Import pgvector registration
try:
    from pgvector.psycopg2 import register_vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    logger.warning("pgvector not available - vector operations will not work")


class DatabaseService:
    """
    SQLAlchemy database service with connection pooling, sessions, and query helpers.

    Implements singleton pattern to ensure only one database connection pool exists
    across the application (API, CLI, worker interfaces).

    Usage patterns:
        # Get singleton instance
        db = DatabaseService.get_instance()

        # Define models using db.Model
        class User(db.Model):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            name = Column(String(50))

        # Create tables
        db.create_all()

        # Query using session_scope context manager
        with db.session_scope() as session:
            user = session.query(User).filter_by(id=1).first()
            users = session.query(User).all()

        # Raw SQL queries
        results = db.execute("SELECT * FROM users WHERE id = :id", {"id": 1})
    """

    _instance = None
    _lock = None

    @classmethod
    def get_instance(cls, **kwargs: Any) -> "DatabaseService":
        """
        Get the singleton instance of DatabaseService.

        Thread-safe singleton implementation. First call initializes the instance
        with provided kwargs, subsequent calls return the existing instance.

        Args:
            **kwargs: Optional arguments for DatabaseService initialization
                     (only used on first call)

        Returns:
            DatabaseService: The singleton instance
        """
        if cls._instance is None:
            # Lazy import to avoid circular dependencies
            from threading import Lock

            if cls._lock is None:
                cls._lock = Lock()

            with cls._lock:
                # Double-checked locking pattern
                if cls._instance is None:
                    cls._instance = cls(**kwargs)

        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.

        Useful for testing to get a fresh instance with different configuration.
        Should not be called in production code.
        """
        if cls._instance is not None:
            cls._instance.close()
            cls._instance = None

    def __init__(
        self,
        database_url: str | None = None,
        pool_size: int | None = None,
        max_overflow: int | None = None,
        echo: bool | None = None,
        **engine_kwargs: Any,
    ):
        conf = config()
        self.database_url = database_url or conf.database_url
        self.pool_size = pool_size if pool_size is not None else conf.database_pool_size
        self.max_overflow = max_overflow if max_overflow is not None else conf.database_max_overflow
        self.echo = echo if echo is not None else conf.database_echo

        if not self.database_url:
            raise ValueError("Database URL is required")

        try:
            self.engine = self._create_engine(**engine_kwargs)
            session_factory = sessionmaker(autocommit=False, autoflush=True, bind=self.engine)
            self.SessionLocal = session_factory
            self.Session = scoped_session(session_factory)

            # Use the shared Base for models
            self.Model = Base

            # Expose metadata for migrations
            self.metadata = Base.metadata

            # Bind the engine to the Base
            Base.metadata.bind = self.engine

            # Register pgvector if available
            if PGVECTOR_AVAILABLE:
                self._register_vector_type()

            logger.info(f"Database service initialized with URL: {self._mask_url(self.database_url)}")
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to initialize database connection: {str(e)}") from e

    def _create_engine(self, **kwargs: Any) -> Engine:
        engine_config = {
            "echo": self.echo,
            "pool_pre_ping": True,
            **kwargs,
        }

        if "poolclass" not in kwargs and "sqlite" not in self.database_url.lower():
            engine_config["pool_size"] = self.pool_size
            engine_config["max_overflow"] = self.max_overflow

        return create_engine(self.database_url, **engine_config)

    def _register_vector_type(self) -> None:
        """Register pgvector type for all new connections."""
        @event.listens_for(self.engine, "connect")
        def connect(dbapi_connection, connection_record):
            try:
                register_vector(dbapi_connection)
            except Exception as e:
                logger.debug(f"pgvector type registration skipped: {e}")
                # Vector operations will still work via SQLAlchemy

    @staticmethod
    def _mask_url(url: str) -> str:
        """Mask password in database URL for safe logging."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            if parsed.password:
                return url.replace(parsed.password, "****")
            return url
        except Exception:
            return "****"

    @property
    def session(self) -> Session:
        """
        Get the thread-local scoped session.

        This property provides Flask-SQLAlchemy style access to sessions.
        The scoped session is automatically managed per-thread and can be
        used directly for queries.

        Example:
            user = db.session.query(User).filter_by(id=1).first()
            db.session.add(user)
            db.session.commit()

        Note: The session is thread-local and persists for the thread lifetime.
        Call remove_session() when done to clean up, or use session_scope()
        context manager for automatic cleanup.
        """
        return self.Session()

    def remove_session(self) -> None:
        """
        Remove the current thread's scoped session.

        Call this after you're done with db.session to clean up the thread-local
        session. Not needed if using session_scope() context manager.
        """
        self.Session.remove()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager for scoped session with auto-commit/rollback.

        Recommended for most use cases. Automatically commits on success,
        rolls back on error, and cleans up the session.
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction error: {str(e)}", exc_info=True)
            raise DatabaseTransactionError(f"Transaction failed: {str(e)}") from e
        finally:
            self.Session.remove()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for non-scoped session with auto-commit/rollback.

        Creates a new session each time (not thread-local). Use when you need
        multiple independent sessions in the same thread.
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}", exc_info=True)
            raise DatabaseTransactionError(f"Transaction failed: {str(e)}") from e
        finally:
            session.close()

    @contextmanager
    def _get_raw_connection(self) -> Generator[Connection, None, None]:
        """Internal connection manager without exception wrapping."""
        connection = self.engine.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _get_raw_transaction(self) -> Generator[Connection, None, None]:
        """Internal transaction manager without exception wrapping."""
        connection = self.engine.connect()
        transaction = connection.begin()
        try:
            yield connection
            transaction.commit()
        except Exception:
            transaction.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def get_connection(self) -> Generator[Connection, None, None]:
        """
        Context manager for raw database connection.

        Use for low-level operations or when you don't need ORM features.
        Connections are lighter weight than sessions.
        """
        connection = self.engine.connect()
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}", exc_info=True)
            raise DatabaseConnectionError(f"Connection failed: {str(e)}") from e
        finally:
            connection.close()

    @contextmanager
    def get_transaction(self) -> Generator[Connection, None, None]:
        """
        Context manager for transactional connection with auto-commit/rollback.

        Use for explicit transaction control with raw SQL. Automatically
        commits on success or rolls back on error.
        """
        connection = self.engine.connect()
        transaction = connection.begin()
        try:
            yield connection
            transaction.commit()
        except Exception as e:
            transaction.rollback()
            logger.error(f"Database transaction error: {str(e)}", exc_info=True)
            raise DatabaseTransactionError(f"Transaction failed: {str(e)}") from e
        finally:
            connection.close()

    def execute(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """
        Execute SQL query and return all results.

        Args:
            query: SQL query string (use :param for parameters)
            params: Optional parameter dictionary

        Returns:
            List of rows if query returns results, else result object
        """
        try:
            with self._get_raw_connection() as conn:
                result = conn.execute(text(query), params or {})
                if result.returns_rows:
                    return result.fetchall()
                return result
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}", exc_info=True)
            raise DatabaseQueryError(f"Query failed: {str(e)}") from e

    def execute_one(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """
        Execute SQL query and return single result or None.

        Args:
            query: SQL query string (use :param for parameters)
            params: Optional parameter dictionary

        Returns:
            Single row if found, None otherwise
        """
        try:
            with self._get_raw_connection() as conn:
                result = conn.execute(text(query), params or {})
                if result.returns_rows:
                    return result.fetchone()
                return None
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}", exc_info=True)
            raise DatabaseQueryError(f"Query failed: {str(e)}") from e

    def execute_many(self, query: str, params_list: list[dict[str, Any]]) -> int:
        """
        Execute SQL query with multiple parameter sets in transaction.

        Args:
            query: SQL query string (use :param for parameters)
            params_list: List of parameter dictionaries

        Returns:
            Number of rows affected (0 if unavailable)

        Raises:
            DatabaseQueryError: If rowcount cannot be determined for operations that require it
        """
        try:
            with self._get_raw_transaction() as conn:
                result = conn.execute(text(query), params_list)
                if hasattr(result, "rowcount") and result.rowcount >= 0:
                    return result.rowcount
                else:
                    # Return 0 for cases where rowcount is not available (e.g., some DDL statements)
                    return 0
        except Exception as e:
            logger.error(f"Batch query execution failed: {str(e)}", exc_info=True)
            raise DatabaseQueryError(f"Batch query failed: {str(e)}") from e

    def test_connection(self) -> bool:
        """Test database connection health."""
        try:
            with self.get_connection() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

    def create_all(self) -> None:
        """Create all tables defined by models inheriting from db.Model."""
        self.Model.metadata.create_all(self.engine)
        logger.info("Created all database tables")

    def drop_all(self) -> None:
        """Drop all tables defined by models inheriting from db.Model."""
        self.Model.metadata.drop_all(self.engine)
        logger.info("Dropped all database tables")

    def close(self) -> None:
        """
        Close all connections and dispose of engine.

        Call this when shutting down the application.
        """
        try:
            self.Session.remove()
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
