from typing import Any, Dict


def safe_eval_expression(code: str, allowed_names: Dict[str, Any]) -> Any:
    """Safely evaluate a single Python expression with restricted AST and names."""
    import ast

    class SafeVisitor(ast.NodeVisitor):
        allowed = (
            ast.Expression, ast.Constant, ast.Num, ast.Str, ast.Bytes,
            ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
            ast.BitXor, ast.USub, ast.UAdd, ast.And, ast.Or,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Call, ast.Load, ast.Name, ast.Tuple, ast.List, ast.Dict,
        )

        def visit(self, node):
            if not isinstance(node, self.allowed):
                raise ValueError(f"Disallowed expression: {type(node).__name__}")
            return super().visit(node)

    try:
        parsed = ast.parse(code, mode="eval")
    except SyntaxError as e:
        raise ValueError("Only single-expression Python is allowed") from e

    SafeVisitor().visit(parsed)

    def ev(node):
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.BinOp):
            a, b = ev(node.left), ev(node.right)
            ops = {ast.Add: a + b, ast.Sub: a - b, ast.Mult: a * b,
                   ast.Div: a / b, ast.Mod: a % b, ast.Pow: a ** b,
                   ast.BitXor: a ^ b}
            return ops[type(node.op)]
        if isinstance(node, ast.UnaryOp):
            v = ev(node.operand)
            return {ast.UAdd: +v, ast.USub: -v}[type(node.op)]
        if isinstance(node, ast.Name):
            if node.id in allowed_names:
                return allowed_names[node.id]
            raise ValueError(f"Name '{node.id}' is not allowed")
        if isinstance(node, ast.Call):
            func = ev(node.func)
            args = [ev(a) for a in node.args]
            return func(*args)
        if isinstance(node, (ast.Tuple, ast.List)):
            return [ev(e) for e in node.elts]
        if isinstance(node, ast.Dict):
            return {ev(k): ev(v) for k, v in zip(node.keys, node.values)}
        if isinstance(node, ast.BoolOp):
            vals = [ev(v) for v in node.values]
            return all(vals) if isinstance(node.op, ast.And) else any(vals)
        if isinstance(node, ast.Compare):
            left = ev(node.left)
            for op, comp in zip(node.ops, node.comparators):
                right = ev(comp)
                checks = {
                    ast.Eq: left == right, ast.NotEq: left != right,
                    ast.Lt: left < right, ast.LtE: left <= right,
                    ast.Gt: left > right, ast.GtE: left >= right,
                }
                if not checks[type(op)]:
                    return False
                left = right
            return True
        raise ValueError("Unsupported expression")

    return ev(parsed)
