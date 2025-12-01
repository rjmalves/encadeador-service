from abc import ABC, abstractmethod
from os import chdir, curdir
from pathlib import Path
from typing import Any

from app.adapters.decomprepository import (
    AbstractDecompRepository,
)
from app.adapters.decomprepository import (
    factory as decomp_factory,
)
from app.adapters.newaverepository import (
    AbstractNewaveRepository,
)
from app.adapters.newaverepository import (
    factory as newave_factory,
)
from app.internal.settings import Settings
from app.models.program import Program


class AbstractUnitOfWork(ABC):
    """
    Abstract Unit of Work for managing case file operations.

    Supports both sync and async context managers for flexibility.
    """

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args: Any) -> None:
        self.rollback()

    async def __aenter__(self) -> "AbstractUnitOfWork":
        """Async context manager entry (for S3 unit of work)."""
        return self.__enter__()

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit (for S3 unit of work)."""
        self.__exit__(*args)

    @abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError

    @property
    @abstractmethod
    def program(self) -> Program:
        raise NotImplementedError

    @property
    @abstractmethod
    def files(
        self,
    ) -> AbstractNewaveRepository | AbstractDecompRepository:
        raise NotImplementedError

    @property
    def output_key(self) -> str | None:
        """S3 key of uploaded output (only for S3 unit of work)."""
        return None

    @property
    def execution_hash(self) -> str | None:
        """Execution hash for this unit of work (only for S3 unit of work)."""
        return None


class NewaveUnitOfWork(AbstractUnitOfWork):
    def __init__(self, directory: str):
        self._current_path = Path(curdir).resolve()
        self._case_directory = directory
        self._newave = None

    def __create_repository(self):
        if self._newave is None:
            self._newave = newave_factory(
                Settings.newave_source, str(self._case_directory)
            )

    def __enter__(self) -> "NewaveUnitOfWork":
        chdir(self._case_directory)
        self.__create_repository()
        uow = super().__enter__()
        assert isinstance(uow, NewaveUnitOfWork)
        return uow

    def __exit__(self, *args):
        chdir(self._current_path)
        super().__exit__(*args)

    @property
    def program(self) -> Program:
        return Program.NEWAVE

    @property
    def files(self) -> AbstractNewaveRepository:
        if not self._newave:
            raise RuntimeError("Newave repository not created")
        return self._newave

    def rollback(self):
        pass


class DecompUnitOfWork(AbstractUnitOfWork):
    def __init__(self, directory: str):
        self._current_path = Path(curdir).resolve()
        self._case_directory = directory
        self._decomp = None

    def __create_repository(self):
        if self._decomp is None:
            self._decomp = decomp_factory(
                Settings.decomp_source, str(self._case_directory)
            )

    def __enter__(self) -> "DecompUnitOfWork":
        chdir(self._case_directory)
        self.__create_repository()
        uow = super().__enter__()
        assert isinstance(uow, DecompUnitOfWork)
        return uow

    def __exit__(self, *args):
        chdir(self._current_path)
        super().__exit__(*args)

    @property
    def program(self) -> Program:
        return Program.DECOMP

    @property
    def files(self) -> AbstractDecompRepository:
        if not self._decomp:
            raise RuntimeError("Decomp repository not created")
        return self._decomp

    def rollback(self):
        pass


def factory(kind: Program, *args, **kwargs) -> AbstractUnitOfWork:
    mappings: dict[Program, type[AbstractUnitOfWork]] = {
        Program.NEWAVE: NewaveUnitOfWork,
        Program.DECOMP: DecompUnitOfWork,
    }
    return mappings[kind](*args, **kwargs)
