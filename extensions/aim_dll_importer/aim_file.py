from typing import Optional

from .aim_file_context_manager import AimFileContextManager
from .aim_session import AimSession


class AimFile:
    _id: int
    _context_manager: AimFileContextManager
    _session: Optional[AimSession]

    def __init__(self, file_idx: int, context_manager: AimFileContextManager):
        """Initialize an AIM file.

        Parameters
        ----------
        file_idx : int
            Identifier of the AIM file.
        context_manager : AimFileContextManager
            Context manager used to access and manage the AIM file.
        """
        self._id = file_idx
        self._context_manager = context_manager

        self._session = None

    def __enter__(self):
        """Enter the AIM file context.

        Returns
        -------
        AimFile
            The current AIM file instance.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the AIM file context and close the file.

        Parameters
        ----------
        exc_type : type, optional
            Exception type, if an exception was raised inside the context.
        exc_value : BaseException, optional
            Exception instance, if an exception was raised inside the
            context.
        traceback : traceback, optional
            Traceback associated with the exception, if one was raised.
        """
        self.close()

    def close(self):
        """Close the AIM file.

        Releases the resources associated with the file through the
        context manager.
        """
        self._context_manager.close_aim_file(self)

    @property
    def id(self) -> int:
        """Return the AIM file identifier.

        Returns
        -------
        int
            The identifier of the AIM file.
        """
        return self._id

    @property
    def context_manager(self) -> AimFileContextManager:
        """Return the context manager associated with the file.

        Returns
        -------
        AimFileContextManager
            The context manager used to access the AIM file.
        """
        return self._context_manager

    @property
    def session(self) -> AimSession:
        """Return the session associated with the AIM file.

        The session is created lazily on first access and cached for
        subsequent accesses.

        Returns
        -------
        AimSession
            The session associated with the AIM file.
        """
        if self._session is None:
            self._session = AimSession(self, self.context_manager)
        return self._session