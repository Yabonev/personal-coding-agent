"""Orchestrator for coordinating chat application components."""

from __future__ import annotations

from ..models.config import ChatConfig
from ..models.tool import StreamResult
from ..processors.stream_response_processor import StreamResponseProcessor
from ..services.chat_api_service import ChatApiService
from ..services.message_repository import MessageRepository
from ..services.tool_executor import ToolExecutor
from ..tracing import span
from ..tracing import trace
from ..tracing import SpanKind
from ..ui.console_output import ConsoleOutput
from ..ui.loading_spinner import LoadingSpinner


class ChatOrchestrator:
    """Orchestrates the chat application workflow."""

    def __init__(self, config: ChatConfig) -> None:
        """Initialize chat orchestrator with configuration.

        Args:
            config: Chat configuration
        """
        self._config = config
        self._api_service = ChatApiService(config)
        self._message_repository = MessageRepository(config.system_prompt)
        self._output_handler = ConsoleOutput()
        self._spinner = LoadingSpinner()
        self._tool_executor = ToolExecutor(tracing_config=config.tracing)
        self._response_processor = StreamResponseProcessor(
            message_repository=self._message_repository,
            output_handler=self._output_handler,
            spinner=self._spinner,
            tracing_config=config.tracing,
        )

    def run(self) -> None:
        """Run the main chat loop."""
        self._output_handler.display_welcome()

        with trace("conversation", config=self._config.tracing):
            while True:
                try:
                    user_input = self._output_handler.get_user_input("")

                    if self._should_exit(user_input):
                        self._output_handler.display_goodbye()
                        break

                    if not user_input:
                        continue

                    self._process_user_message(user_input)

                except KeyboardInterrupt:
                    self._output_handler.display_goodbye()
                    break
                except Exception as e:
                    self._output_handler.display_error(str(e))

    def _should_exit(self, user_input: str) -> bool:
        """Check if user wants to exit."""
        return user_input.lower() in ["exit", "quit", "bye"]

    def _process_user_message(self, user_input: str) -> None:
        """Process a user message and get response.

        Args:
            user_input: User's input message
        """
        with span("turn", kind=SpanKind.TURN) as s:
            s.set(model=self._config.model)
            self._message_repository.add_user_message(user_input)
            self._complete_with_tools()

    def _complete_with_tools(self) -> None:
        """Run completion loop, handling tool calls until done."""
        while True:
            self._spinner.start()

            try:
                messages = self._message_repository.get_messages_for_api()

                with self._api_service.streaming_completion(messages) as response:
                    result = self._response_processor.process(response)

                    if result.has_tool_calls:
                        self._execute_tool_calls(result)

                if not result.has_tool_calls:
                    break

            except Exception:
                self._spinner.stop()
                raise

    def _execute_tool_calls(self, result: StreamResult) -> None:
        """Execute tool calls and add results to message repository."""
        self._message_repository.add_assistant_tool_calls(result.tool_calls)

        for tool_call in result.tool_calls:
            tool_result = self._tool_executor.execute(tool_call)

            self._output_handler.display_tool_result(
                tool_result.content,
                tool_result.is_error,
            )

            self._message_repository.add_tool_result(tool_result)
