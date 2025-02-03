from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain.agents import AgentExecutor, create_tool_calling_agent


from operator import itemgetter
from typing import Dict, Any


from fin_advisor_llm_api.app.prompts.prompt import generate_system_prompt, reflective_system_prompt, TOOL_AGENT_PROMPT
from fin_advisor_llm_api.app.tools.tool import *

import logging


logger = logging.getLogger(__name__)


critique_output =""
load_dotenv()
llm = ChatOpenAI(temperature=0)

# Database configuration
postgres_memory_url = "postgresql+psycopg://neondb_owner:npg_y8IjUwmbv0sW@ep-flat-glade-a4m83cg4-pooler.us-east-1.aws.neon.tech/neondb"

# Initialize prompts
generate_prompt = ChatPromptTemplate.from_messages([
    ("system", generate_system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}")
])

# Updated reflective prompt to match expected variables
reflective_prompt = ChatPromptTemplate.from_messages([
    ("system", reflective_system_prompt),
    MessagesPlaceholder(variable_name="history"),
    ("human", "Please evaluate this financial advice: {generated_output}")
])

def get_history(inputs: Dict[str, Any]) -> list:
    """Get history with default empty list if not present"""
    return inputs.get("history", [])

# Initialize chains
generate_chain = (
    {
        "question": itemgetter("question"),
        "history": itemgetter("history"),
        "critique_output": itemgetter("critique_output")
    }
    | generate_prompt
    | llm
    | StrOutputParser()
)

reflective_chain = (
    {
        "question": itemgetter("question"),
        "history": itemgetter("history"),
        "generated_output": itemgetter("generated_output"),
    }
    | reflective_prompt
    | llm
    | StrOutputParser()
)

# Initialize chain with history
generate_chain_with_history = RunnableWithMessageHistory(
    generate_chain,
    lambda session_id: SQLChatMessageHistory(
        connection_string=postgres_memory_url,
        session_id=session_id
    ),
    input_messages_key="question",
    history_messages_key="history",
    critique_messages_key="critique_output"
)

reflective_chain_with_history = RunnableWithMessageHistory(
    reflective_chain,
    lambda session_id: SQLChatMessageHistory(
        connection_string=postgres_memory_url,
        session_id=session_id
    ),
    input_messages_key="question",
    history_messages_key="history",
    generated_messages_key="generated_output"
)




def reflective_stream_chain(question, config, n_runs=2):
    critique_output = ""
    logs = {
        'generation': {},
        'reflection': {}
    }
    for step in range(n_runs):
        first_response = generate_chain_with_history.invoke(
            {"question": question, "critique_output": critique_output},
            config = config
        )

        logs['generation'][f'iter_{step}'] = first_response

        critique_response = reflective_chain_with_history.invoke(
            { "question": question  ,"generated_output": first_response},
            config=config
        )
        logs['reflection'][f'iter_{step}'] = critique_response
    return critique_response, logs

tools = [
    stock_price_fetcher,
    crypto_price_fetcher,
    currency_converter,
    savings_plan_calculator,
    tax_calculator,
    loan_eligibility_checker,
    retirement_planner,
    market_news_fetcher,
    investment_risk_assessor
]





tool_agent_prompt = ChatPromptTemplate.from_messages([
    ("system", TOOL_AGENT_PROMPT),
    ("human", "{input}"),
    ("ai", "{agent_scratchpad}")
])







# response1 = agent_executor.invoke({"input": "Fetch the latest financial news headlines."})
# print(response1)



# Function to capture verbose logs and return them
def tool_agent_chain(question, config):
    # Create agent
    agent = create_tool_calling_agent(llm, tools, tool_agent_prompt)
    # Create executor
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)
    try:
        response = agent_executor.invoke(
            {"input": question},
            config=config,
        )
        print("resdponse", response)
    except Exception as e:
        response = {"error": str(e)}

    return {"response": response, "logs": response["intermediate_steps"]}
