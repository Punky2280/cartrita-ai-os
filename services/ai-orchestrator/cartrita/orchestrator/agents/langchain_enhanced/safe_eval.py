from typing import Any, Dict


def safe_eval_expression(code: str, allowed_names: Dict[str, Any]) -> Any:
    """Safely evaluate a single Python expression with restricted AST and names."""
    import ast

    class SafeVisitor(ast.NodeVisitor):
        allowed = (
            ast.Expression,
            ast.Constant,
            ast.Num,
            ast.Str,
            ast.Bytes,
            ast.BinOp,
            ast.UnaryOp,
            ast.BoolOp,
            ast.Compare,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.BitXor,
            ast.USub,
            ast.UAdd,
            ast.And,
            ast.Or,
            ast.Eq,
            ast.NotEq,
            ast.Lt,
            ast.LtE,
            ast.Gt,
            ast.GtE,
            ast.Call,
            ast.Load,
            ast.Name,
            ast.Tuple,
            ast.List,
            ast.Dict,
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

    # Handlers to reduce ev() complexity and avoid eager evaluation
    def _handle_expression(node):
        return ev(node.body)

    def _handle_constant(node):
        return node.value

    def _handle_num(node):
        return node.n

    def _handle_str(node):
        return node.s

    def _handle_bytes(node):
        return node.s

    def _handle_binop(node):
        a, b = ev(node.left), ev(node.right)
        op = node.op
        if isinstance(op, ast.Add):
            return a + b
        elif isinstance(op, ast.Sub):
            return a - b
        elif isinstance(op, ast.Mult):
            return a * b
        elif isinstance(op, ast.Div):
            return a / b
        elif isinstance(op, ast.Mod):
            return a % b
        elif isinstance(op, ast.Pow):
            return a**b
        elif isinstance(op, ast.BitXor):
            return a ^ b
        raise ValueError("Unsupported binary operator")

    def _handle_unaryop(node):
        v = ev(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +v
        elif isinstance(node.op, ast.USub):
            return -v
        raise ValueError("Unsupported unary operator")

    def _handle_name(node):
        if node.id in allowed_names:
            return allowed_names[node.id]
        raise ValueError(f"Name '{node.id}' is not allowed")

    def _handle_call(node):
        func = ev(node.func)
        args = [ev(a) for a in node.args]
        return func(*args)

    def _handle_sequence(node):
        return [ev(e) for e in node.elts]

    def _handle_dict(node):
        return {ev(k): ev(v) for k, v in zip(node.keys, node.values)}

    def _handle_boolop(node):
        if isinstance(node.op, ast.And):
            for v in node.values:
                if not ev(v):
                    return False
            return True
        # ast.Or
        for v in node.values:
            if ev(v):
                return True
        return False

    def _handle_compare(node):
        left = ev(node.left)
        for op, comp in zip(node.ops, node.comparators):
            right = ev(comp)
            if isinstance(op, ast.Eq):
                ok = left == right
            elif isinstance(op, ast.NotEq):
                ok = left != right
            elif isinstance(op, ast.Lt):
                ok = left < right
            elif isinstance(op, ast.LtE):
                ok = left <= right
            elif isinstance(op, ast.Gt):
                ok = left > right
            elif isinstance(op, ast.GtE):
                ok = left >= right
            else:
                raise ValueError("Unsupported comparison operator")
            if not ok:
                return False
            left = right
        return True

    def ev(node):
        node_type = type(node)
        handler = direct_handlers.get(node_type)
        if handler is not None:
            return handler(node)
        if isinstance(node, (ast.Tuple, ast.List)):
            return _handle_sequence(node)
        raise ValueError("Unsupported expression")

    direct_handlers = {
        ast.Expression: _handle_expression,
        ast.Constant: _handle_constant,
        ast.Num: _handle_num,
        ast.Str: _handle_str,
        ast.Bytes: _handle_bytes,
        ast.BinOp: _handle_binop,
        ast.UnaryOp: _handle_unaryop,
        ast.Name: _handle_name,
        ast.Call: _handle_call,
        ast.Dict: _handle_dict,
        ast.BoolOp: _handle_boolop,
        ast.Compare: _handle_compare,
    }

    return ev(parsed)
