from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_openrouter import ChatOpenRouter

from app.config.settings import settings


def build_agent(tools: list) -> AgentExecutor:
    llm = ChatOpenRouter(
        model=settings.openrouter_model,
        temperature=0,
        api_key=settings.openrouter_api_key or settings.openai_api_key,
        base_url=settings.openrouter_base_url,
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Act as the virtual waiter for Chillazi Food Court. "
            "Use the provided tools whenever the user asks about the menu, a menu item, cart contents, checkout, or order status. "
            "Do not invent menu data when a tool can provide it. "
            "Before checkout, always collect a delivery address and an order note. "
            "If the user wants to place an order, confirm the items and quantities before finalizing it. "
            "You may answer directly only for simple greetings or general guidance that does not require data lookup.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=settings.debug,
        max_iterations=20,
        handle_parsing_errors=True,
        return_intermediate_steps=False,
    )
