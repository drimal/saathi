from langchain_ollama import ChatOllama
from langchain_community.tools.ddg_search.tool import DuckDuckGoSearchResults
from langchain import hub
from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from typing import Dict
import os


class OllamaAgentManager:
    def __init__(self, llm: ChatOllama) -> None:
        """
        Initializes the OllamaAgentManager, which sets up the tools and agent needed for the Ollama chat client.

        Args:
            llm (ChatOllama): The language model object initialized from the ChatOllama class.
        """
        self.llm = llm
        self.tools = self._initialize_tools()
        self.fc_prompt = self._fetch_fc_prompt()
        self.message_history = self._initialize_message_history()
        self.agent_executor = self._create_agent_executor()

    def _fetch_fc_prompt(self) -> str:
        """
        Fetches the function-calling prompt from LangChain's hub.

        Returns:
            str: The function-calling prompt to be used by the agent.
        """
        return hub.pull(
            "hwchase17/openai-functions-agent", api_key=os.environ["LANGSMITH_API_KEY"]
        )

    def _initialize_message_history(self) -> ChatMessageHistory:
        """
        Initializes a message history object to store chat interactions.

        Returns:
            ChatMessageHistory: Object to maintain message history.
        """
        return ChatMessageHistory()

    def _initialize_tools(self) -> list:
        """
        Initializes the tools available for the agent, such as the DuckDuckGo search tool.

        Returns:
            list: A list of tools that the agent can use.
        """
        search_tool = DuckDuckGoSearchResults(max_results=3)
        return [search_tool]

    def _create_agent_executor(self) -> AgentExecutor:
        """
        Creates an agent executor that integrates the LLM with the tools and function-calling prompt.

        Returns:
            AgentExecutor: The agent executor to manage the agent's execution with tools.
        """
        agent = create_tool_calling_agent(self.llm, self.tools, self.fc_prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=False, stream=False)


class OllamaChatClient:
    def __init__(self, model: str, session_id: str, model_params: Dict) -> None:
        """
        Initializes the OllamaChatClient with the specified model and session.

        Args:
            model (str): The name of the Ollama model to use.
            session_id (str): Unique identifier for the chat session.
            model_params (Dict): Parameters to configure the language model.
        """
        # Initialize the LLM using the provided model and parameters
        self.llm = ChatOllama(model=model, **model_params)
        self.session_id = session_id

        # Use the OllamaAgentManager to set up tools, agent, and message history
        self.agent_manager = OllamaAgentManager(self.llm)

        # Create a Runnable with message history to manage multi-turn conversations
        self.agent_with_chat_history = RunnableWithMessageHistory(
            self.agent_manager.agent_executor,
            lambda _: self.agent_manager.message_history,  # In-memory message history
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    def get_completion(self, message: str) -> str:
        """
        Retrieves a completion from the model for the given message input.

        Args:
            message (str): The input message to send to the model.

        Returns:
            str: The model's response to the input message.
        """
        # Invoke the agent with the input message and session ID
        response = self.agent_with_chat_history.invoke(
            {"input": message}, config={"configurable": {"session_id": self.session_id}}
        )["output"]

        return response
