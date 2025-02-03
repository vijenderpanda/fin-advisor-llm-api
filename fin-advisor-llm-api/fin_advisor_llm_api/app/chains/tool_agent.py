from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from fin_advisor_llm_api.app.tools.tool import *
# Initialize LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Define available tools
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

# Create agent
agent = create_tool_calling_agent(llm, tools)

# Create executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)





