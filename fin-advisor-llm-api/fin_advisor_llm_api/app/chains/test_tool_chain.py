from langchain.tools import tool
from dotenv import load_dotenv
import requests

load_dotenv()


@tool
def stock_price_fetcher(symbol: str) -> str:
    """
    Fetches real-time stock price for a given symbol using Alpha Vantage API.
    Requires a free API key from https://www.alphavantage.co/support/#api-key

    Args:
        symbol (str): The stock symbol (e.g., AAPL, TSLA, MSFT).

    Returns:
        str: The stock price or an error message.
    """
    API_KEY = "YKDBO357X2FYJV65"
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()

        if "Global Quote" in data and "05. price" in data["Global Quote"]:
            price = data["Global Quote"]["05. price"]
            return f"The current price of {symbol} is **${price}**."
        
        elif "Note" in data:
            return "API rate limit exceeded. Please wait and try again."

        return "Stock data not found. Check the symbol and try again."
    
    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"

@tool
def crypto_price_fetcher(crypto: str) -> str:
    """
    Fetches real-time cryptocurrency price using the CoinGecko API.
    No API key is required.

    Args:
        crypto (str): Cryptocurrency name (e.g., 'bitcoin', 'ethereum').

    Returns:
        str: The current price of the cryptocurrency in USD.
    """
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto}&vs_currencies=usd"

    try:
        response = requests.get(url)
        data = response.json()

        if crypto in data and "usd" in data[crypto]:
            price = data[crypto]["usd"]
            return f"The current price of {crypto.capitalize()} is **${price}**."
        return "Cryptocurrency not found. Check the name and try again."

    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"

@tool
def currency_converter(amount: float, from_currency: str, to_currency: str) -> str:
    """
    Converts an amount from one currency to another using ExchangeRate-API.

    Args:
        amount (float): Amount to be converted.
        from_currency (str): Source currency (e.g., 'USD', 'INR').
        to_currency (str): Target currency (e.g., 'EUR', 'GBP').

    Returns:
        str: Converted amount with exchange rate details.
    """
    API_KEY = "bbbc65db3de68e646ed8eb3b"

    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/{from_currency.upper()}"

    try:
        response = requests.get(url)
        data = response.json()

        if "conversion_rates" in data and to_currency.upper() in data["conversion_rates"]:
            rate = data["conversion_rates"][to_currency.upper()]
            converted_amount = round(amount * rate, 2)
            return f"{amount} {from_currency.upper()} is equivalent to **{converted_amount} {to_currency.upper()}** at the current exchange rate of {rate}."

        return "Currency conversion failed. Check currency codes and try again."

    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"

@tool
def savings_plan_calculator(income: float, savings_goal: float, months: int) -> str:
    """Calculates monthly savings needed to reach a goal."""
    monthly_savings = savings_goal / months
    percent_of_income = (monthly_savings / income) * 100
    return (f"To save ₹{savings_goal:,} in {months} months, "
            f"you should save ₹{monthly_savings:.2f}/month, "
            f"which is {percent_of_income:.2f}% of your income.")

@tool
def tax_calculator(income: float) -> str:
    """Estimates tax liability based on Indian tax slabs."""
    tax_brackets = [(250000, 0), (500000, 0.05), (1000000, 0.2), (float('inf'), 0.3)]
    
    tax = 0
    prev_limit = 0
    for limit, rate in tax_brackets:
        if income > limit:
            tax += (limit - prev_limit) * rate
        else:
            tax += (income - prev_limit) * rate
            break
        prev_limit = limit

    return f"Estimated tax liability for ₹{income:,} is ₹{tax:,.2f}."

@tool
def loan_eligibility_checker(income: float, existing_loans: float, credit_score: int) -> str:
    """Checks if a user is eligible for a loan based on income, liabilities, and credit score."""
    if credit_score < 650:
        return "Loan eligibility: LOW due to poor credit score."
    max_loan_amount = income * 12 - existing_loans
    return f"Based on your income of ₹{income:,} and credit score of {credit_score}, you may be eligible for a loan up to ₹{max_loan_amount:,}."

@tool
def retirement_planner(age: int, monthly_savings: float, target_retirement_age: int) -> str:
    """Provides retirement savings advice based on current savings and target age."""
    years_remaining = target_retirement_age - age
    total_savings = years_remaining * 12 * monthly_savings
    return (f"If you save ₹{monthly_savings}/month until age {target_retirement_age}, "
            f"you will have ₹{total_savings:,} saved for retirement.")

@tool
def market_news_fetcher() -> str:
    """
    Fetches the latest financial news headlines using NewsAPI.

    Returns:
        str: A formatted string of the latest market news headlines.
    """
    NEWS_API_KEY = "88efff8404f844f2802a7e5893346868"
    url = f"https://newsapi.org/v2/top-headlines?category=business&language=en&apiKey={NEWS_API_KEY}"

    try:
        response = requests.get(url)
        data = response.json()

        if "articles" in data:
            headlines = [f"🔹 {article['title']}" for article in data["articles"][:5]]  # Get top 5 news
            return "\n".join(headlines) if headlines else "No financial news available at the moment."

        return "Failed to fetch news. Please try again later."

    except requests.exceptions.RequestException as e:
        return f"Network error: {str(e)}"

@tool
def investment_risk_assessor(risk_tolerance: str, investment_amount: float) -> str:
    """Assesses risk level and suggests investment types."""
    risk_map = {
        "low": "Consider bonds, fixed deposits, or blue-chip stocks.",
        "medium": "Consider index funds, ETFs, or diversified mutual funds.",
        "high": "You can explore growth stocks, cryptocurrencies, or venture investments."
    }
    return risk_map.get(risk_tolerance.lower(), "Please provide a valid risk level (low/medium/high).")







from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
# from fin_advisor_llm_api.app.tools.tool import *
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

from langchain import hub

# Get the prompt from LangChain hub or create a custom one
prompt = hub.pull("hwchase17/openai-functions-agent")



# Create agent
agent = create_tool_calling_agent(llm, tools, prompt)
# Create executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


# Example usage
# response1 = agent_executor.invoke({"input": "What is the price of Bitcoin?"})
# print(response1)

# response2 = agent_executor.invoke({"input": "What is the price of Ethereum?"})
# print(response2)

# response3 = agent_executor.invoke({"input": "How much is 1 Dogecoin worth right now?"})
# print(response3)

# response4 = agent_executor.invoke({"input": "What is the current price of Solana?"})
# print(response4)
# Example usage
# response1 = agent_executor.invoke({"input": "What is the stock price of Tesla?"})
# print(response1)

# response2 = agent_executor.invoke({"input": "How much tax should I pay on an income of 12,00,000 INR?"})
# print(response2)

# response3 = agent_executor.invoke({"input": "I want to save ₹5,00,000 in 12 months. My monthly income is ₹1,00,000. How much should I save each month?"})
# print(response3)

# response4 = agent_executor.invoke({"input": "Am I eligible for a loan if my income is ₹50,000, existing loans ₹1,00,000, and credit score is 720?"})
# print(response4)



# currnecy converter


# Example Usage
# response1 = agent_executor.invoke({"input": "Convert 100 USD to INR"})
# print(response1)

# response2 = agent_executor.invoke({"input": "How much is 50 EUR in GBP?"})
# print(response2)

# response3 = agent_executor.invoke({"input": "I want to convert 500 JPY to USD."})
# print(response3)


#  News Fetcher Examples


# Example Usage
response1 = agent_executor.invoke({"input": "Fetch the latest financial news headlines."})
print(response1)

response2 = agent_executor.invoke({"input": "Give me today's stock market news."})
print(response2)

response3 = agent_executor.invoke({"input": "What are the top business headlines today?"})
print(response3)

