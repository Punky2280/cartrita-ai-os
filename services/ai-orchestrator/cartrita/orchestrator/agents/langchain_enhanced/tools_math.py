from .base_tool import AdvancedCartritaTool, ToolCategory


class MathCalculatorTool(AdvancedCartritaTool):
    name: str = "math_calculator"
    description: str = "Perform mathematical calculations and evaluations"
    category: ToolCategory = ToolCategory.COMPUTATION
    cost_factor: float = 0.1

    def do_execute(self, *args, **kwargs) -> str:
        import ast
        import math
        import operator

        if kwargs.get("expression") is not None:
            expression = str(kwargs["expression"])
        elif args:
            expression = str(args[0])
        else:
            raise ValueError("expression is required")

        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg,
        }
        fun = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "log": math.log,
            "exp": math.exp,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "pi": math.pi,
            "e": math.e,
        }

        def ev(n):
            if isinstance(n, ast.Num):
                return n.n
            if isinstance(n, ast.BinOp):
                return ops[type(n.op)](ev(n.left), ev(n.right))
            if isinstance(n, ast.UnaryOp):
                return ops[type(n.op)](ev(n.operand))
            if isinstance(n, ast.Name):
                return fun.get(n.id, 0)
            if isinstance(n, ast.Call):
                f = n.func.id
                if f in fun:
                    return fun[f](*[ev(a) for a in n.args])
            raise TypeError(f"Unsupported operation: {n}")

        try:
            return f"Result: {ev(ast.parse(expression, mode='eval').body)}"
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {e}")
