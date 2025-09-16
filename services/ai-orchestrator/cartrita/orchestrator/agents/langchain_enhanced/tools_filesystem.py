from .base_tool import AdvancedCartritaTool, ToolCategory


class FileSystemTool(AdvancedCartritaTool):
    name: str = "file_system"
    description: str = "Perform safe file system operations"
    category: ToolCategory = ToolCategory.FILE_SYSTEM
    cost_factor: float = 0.2
    rate_limit: int = 30

    def do_execute(self, *args, **kwargs) -> str:
        import tempfile
        from pathlib import Path

        if args and len(args) >= 2:
            operation = str(args[0])
            path = str(args[1])
            content = str(args[2]) if len(args) >= 3 and args[2] is not None else kwargs.get("content")
        else:
            operation = str(kwargs.get("operation"))
            path = str(kwargs.get("path"))
            content = kwargs.get("content")

        if not operation or not path:
            return "operation and path are required"

        safe_base = Path(tempfile.gettempdir()) / "cartrita_workspace"
        safe_base.mkdir(exist_ok=True)
        target_path = safe_base / Path(path).name

        def op_read():
            if target_path.exists():
                return target_path.read_text()
            return f"File {target_path} does not exist"

        def op_write():
            if content is not None:
                target_path.write_text(str(content))
                return f"Successfully wrote to {target_path}"
            return "Content is required for write operation"

        def op_list():
            if target_path.is_dir():
                files = [f.name for f in target_path.iterdir()]
                return f"Contents: {', '.join(files)}"
            return f"{target_path} is not a directory"

        def op_delete():
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                    return f"Deleted file {target_path}"
                return "Cannot delete directories for safety"
            return f"File {target_path} does not exist"

        dispatch = {"read": op_read, "write": op_write, "list": op_list, "delete": op_delete}
        handler = dispatch.get(operation)
        if not handler:
            return f"Unsupported operation: {operation}"
        return handler()
