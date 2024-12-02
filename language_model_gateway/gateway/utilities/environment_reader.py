class EnvironmentReader:
    @staticmethod
    def is_truthy(value: str | bool | int | None) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value.lower() in ("true", "1")
        return bool(value)
