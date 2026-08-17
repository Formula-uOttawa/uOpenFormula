import ctypes
from typing import Callable, Any

from .aim_dll_wrapper_exceptions import (
    AimDLLWrapperFunctionDoesNotExistError,
    AimDLLWrapperException
)
from .function_prototypes import (
    AIM_DLL_FUNCTION_PROTOTYPES,
)


class AimDLLFunctionRegistry:
    """Registry of typed function pointers bound to a loaded DLL.

    Each entry in ``AIM_DLL_FUNCTION_PROTOTYPES`` is expected to be a
    ``ctypes.CFUNCTYPE`` prototype. During initialization, each prototype is
    bound to the corresponding exported function in the DLL and stored in a
    registry for later lookup.
    """

    _dll: ctypes.CDLL
    _function_registry: dict[str, Callable[..., Any]]

    def __init__(self, dll: ctypes.CDLL) -> None:
        """Bind all known function prototypes to the loaded DLL.

        Args:
            dll: The loaded ``ctypes.CDLL`` instance containing the exported
                functions.
        """
        self._dll = dll
        self._function_registry = {}

        self._register_all_prototypes(AIM_DLL_FUNCTION_PROTOTYPES)

    def _register_all_prototypes(
        self,
        function_prototypes: dict[str, Any],
    ) -> None:
        """Bind every prototype to its DLL function.

        Each prototype is already a ``CFUNCTYPE`` class, so calling it with
        ``(function_name, self._dll)`` creates a typed function pointer.
        """
        for function_name, prototype in function_prototypes.items():
            # Create a typed callable bound to the DLL export.
            function = prototype((function_name, self._dll))
            self._register_function(function_name, function)

    def _register_function(
        self,
        function_name: str,
        function: Callable[..., Any],
    ) -> None:
        """Store a bound function in the registry.

        Raises:
            ValueError: If a function with the same name is already registered.
        """
        if function_name in self._function_registry:
            raise ValueError(
                f"Function '{function_name}' is already registered."
            )

        self._function_registry[function_name] = function

    def get_function(self, function_name: str) -> Callable[..., Any]:
        """Retrieve a registered DLL function by name.

        Args:
            function_name: Name of the exported DLL function.

        Returns:
            The typed ctypes function pointer.

        Raises:
            KeyError: If the function has not been registered.
        """
        if function_name not in self._function_registry:
            raise AimDLLWrapperFunctionDoesNotExistError(
                f"Function '{function_name}' is not registered."
            )

        callable_ = self._function_registry[function_name]

        def aim_dll_callable(*args: Any, **kwargs: Any) -> Any:
            try:
                return callable_(*args, **kwargs)
            except Exception as e:
                raise AimDLLWrapperException(e)

        return aim_dll_callable