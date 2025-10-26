from typing import Protocol, Any


class DatasetRepository(Protocol):
    def load_many(self, paths: list[str]) -> Any: ...
    def save_lazy(self, table: Any, path: str) -> None: ...


class Transformer(Protocol):
    def run(self, lf: Any) -> Any: ...


class Aggregator(Protocol):
    def aggregate(self, lf: Any) -> Any: ...
