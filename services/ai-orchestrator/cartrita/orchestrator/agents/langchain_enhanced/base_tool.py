import time
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import ConfigDict

# Optional LangChain imports with fallbacks
try:
    from langchain.pydantic_v1 import BaseModel  # type: ignore
    from langchain.tools import BaseTool  # type: ignore

    LANGCHAIN_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency path
    LANGCHAIN_AVAILABLE = False
    try:
        from pydantic.v1 import BaseModel  # type: ignore
    except Exception:  # pragma: no cover
        from pydantic import BaseModel  # type: ignore

    class BaseTool:  # type: ignore
        name: str
        description: str

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __call__(self, *args, **kwargs):
            return self._run(*args, **kwargs)


class ToolCategory(str, Enum):
    COMPUTATION = "computation"
    DATA_ACCESS = "data_access"
    COMMUNICATION = "communication"
    FILE_SYSTEM = "file_system"
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    MULTIMEDIA = "multimedia"
    SYSTEM = "system"


class ToolMetrics(BaseModel):
    name: str
    total_calls: int = 0
    success_rate: float = 1.0
    average_execution_time: float = 0.0
    last_used: Optional[datetime] = None
    error_count: int = 0


class AdvancedCartritaTool(BaseTool):
    category: ToolCategory
    cost_factor: float = 1.0
    rate_limit: Optional[int] = None
    dependencies: List[str] = []
    version: str = "1.0"
    author: Optional[str] = None

    _metrics: Optional[ToolMetrics] = None
    _last_call_time: Optional[float] = None
    _call_history: List[float] = []
    # TODO[pydantic]: The following keys were removed: `underscore_attrs_are_private`.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-config for more information.
    model_config = ConfigDict(
        arbitrary_types_allowed=True, underscore_attrs_are_private=True
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, "_metrics") or self._metrics is None:
            self._metrics = ToolMetrics(
                name=getattr(self, "name", self.__class__.__name__)
            )
        self._metrics.name = getattr(self, "name", self.__class__.__name__)
        self._call_history = []

    def do_execute(self, *args, **kwargs) -> Any:  # pragma: no cover - abstract hook
        raise NotImplementedError

    def _run(self, *args, run_manager: Optional[Any] = None, **kwargs: Any) -> str:
        if not self._check_rate_limit():
            return f"Rate limit exceeded for tool {self.name}. Please wait."

        start_time = time.time()
        self._last_call_time = start_time
        self._call_history.append(start_time)
        cutoff_time = start_time - 3600
        self._call_history = [t for t in self._call_history if t > cutoff_time]

        try:
            if run_manager:
                run_manager.on_text(f"Executing {self.name}...\n", color="blue")
            result = self.do_execute(*args, **kwargs)
            exec_time = time.time() - start_time
            self._update_metrics(True, exec_time)
            if run_manager:
                run_manager.on_text(f"Completed in {exec_time:.2f}s\n", color="green")
            return str(result)
        except Exception as e:  # pragma: no cover - runtime path
            exec_time = time.time() - start_time
            self._update_metrics(False, exec_time, str(e))
            if run_manager:
                run_manager.on_text(f"Error: {str(e)}\n", color="red")
            return f"Tool execution failed: {str(e)}"

    async def _arun(
        self, *args, run_manager: Optional[Any] = None, **kwargs: Any
    ) -> str:
        if not self._check_rate_limit():
            return f"Rate limit exceeded for tool {self.name}. Please wait."

        start_time = time.time()
        self._last_call_time = start_time
        self._call_history.append(start_time)
        cutoff_time = start_time - 3600
        self._call_history = [t for t in self._call_history if t > cutoff_time]

        try:
            if run_manager:
                await run_manager.on_text(f"Executing {self.name}...\n", color="blue")
            result = self.do_execute(*args, **kwargs)
            exec_time = time.time() - start_time
            self._update_metrics(True, exec_time)
            if run_manager:
                await run_manager.on_text(
                    f"Completed in {exec_time:.2f}s\n", color="green"
                )
            return str(result)
        except Exception as e:  # pragma: no cover
            exec_time = time.time() - start_time
            self._update_metrics(False, exec_time, str(e))
            if run_manager:
                await run_manager.on_text(f"Error: {str(e)}\n", color="red")
            return f"Tool execution failed: {str(e)}"

    def _execute(self, *args, **kwargs) -> Any:
        return self.do_execute(*args, **kwargs)

    def _check_rate_limit(self) -> bool:
        if not self.rate_limit:
            return True
        now = time.time()
        recent = [t for t in self._call_history if t > now - 60]
        return len(recent) < self.rate_limit

    def _update_metrics(
        self, success: bool, execution_time: float, error: Optional[str] = None
    ) -> None:
        if self._metrics is None:
            self._metrics = ToolMetrics(
                name=getattr(self, "name", self.__class__.__name__)
            )

        self._metrics.total_calls += 1
        self._metrics.last_used = datetime.now()
        if not success:
            self._metrics.error_count += 1
        self._metrics.success_rate = (
            self._metrics.total_calls - self._metrics.error_count
        ) / self._metrics.total_calls
        total_time = self._metrics.average_execution_time * (
            self._metrics.total_calls - 1
        )
        self._metrics.average_execution_time = (
            total_time + execution_time
        ) / self._metrics.total_calls

    def get_metrics(self) -> ToolMetrics:
        if self._metrics is None:
            self._metrics = ToolMetrics(
                name=getattr(self, "name", self.__class__.__name__)
            )
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        self._metrics = ToolMetrics(name=getattr(self, "name", self.__class__.__name__))
        self._call_history = []
