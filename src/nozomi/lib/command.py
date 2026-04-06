from abc import ABC, abstractmethod
from argparse import Namespace


class BaseCommand(ABC):
    @abstractmethod
    def register_options(self, subparsers) -> None:
        pass

    @abstractmethod
    def command(self, args: Namespace) -> int:
        pass

    @abstractmethod
    def get_command_str(self) -> str:
        pass
