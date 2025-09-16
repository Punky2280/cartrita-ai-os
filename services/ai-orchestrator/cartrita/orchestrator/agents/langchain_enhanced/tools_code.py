from .base_tool import AdvancedCartritaTool, ToolCategory
from .safe_eval import safe_eval_expression


class CodeExecutorTool(AdvancedCartritaTool):
    name: str = "code_executor"
    description: str = "Execute code safely in sandboxed environment"
    category: ToolCategory = ToolCategory.CODE_EXECUTION
    cost_factor: float = 3.0
    rate_limit: int = 5

    def do_execute(self, *args, **kwargs) -> str:
        if args:
            code = str(args[0])
            language = str(args[1]) if len(args) > 1 else str(kwargs.get("language", "python"))
        else:
            code = str(kwargs.get("code"))
            language = str(kwargs.get("language", "python"))

        if not code:
            return "code is required"
        if language.lower() != "python":
            return f"Language {language} not supported. Only Python is available."

        import math as _math
        allowed = {
            'len': len, 'str': str, 'int': int, 'float': float, 'abs': abs, 'round': round,
            'min': min, 'max': max, 'sum': sum, 'range': range, 'enumerate': enumerate,
            'zip': zip, 'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
            'pi': _math.pi, 'e': _math.e, 'sin': _math.sin, 'cos': _math.cos, 'tan': _math.tan,
            'sqrt': _math.sqrt, 'log': _math.log, 'exp': _math.exp,
        }
        try:
            return str(safe_eval_expression(code, allowed))
        except Exception as e:
            return f"Execution error: {e}"
