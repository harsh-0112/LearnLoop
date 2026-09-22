"""Fake Anthropic client helpers for tests."""

from dataclasses import dataclass, field


@dataclass
class FakeTextBlock:
    text: str


@dataclass
class FakeMessage:
    content: list[FakeTextBlock]


@dataclass
class FakeMessages:
    responses: list[str]
    calls: list[dict] = field(default_factory=list)

    def create(self, **kwargs) -> FakeMessage:
        self.calls.append(kwargs)
        index = min(len(self.calls) - 1, len(self.responses) - 1)
        return FakeMessage(content=[FakeTextBlock(text=self.responses[index])])


@dataclass
class FakeAnthropic:
    """Returns each canned response in turn; repeats the last one if called again."""

    responses: list[str]

    def __post_init__(self) -> None:
        self.messages = FakeMessages(responses=self.responses)
