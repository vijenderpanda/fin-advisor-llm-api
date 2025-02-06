from langchain.tools import tool
import requests
import random
import json
from datetime import datetime


@tool
def stock_price_fetcher(query: str) -> str:
    """Fetch real-time stock prices.
    Query format: 'symbol: STOCK_SYMBOL'
    For Indian stocks, add .NS for NSE listings (e.g., TCS.NS)
    """
    try:
        symbol = query.split(':')[1].strip()
        
        # Add .NS suffix for NSE stocks if not present
        if not symbol.endswith('.NS') and not symbol.endswith('.BO'):
            symbol = f"{symbol}.NS"
        
        # Using Alpha Vantage API (requires free API key)
        API_KEY = "5JU1BLZLJCL0WLJ8"
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            price = float(quote.get("05. price", 0))
            change = float(quote.get("09. change", 0))
            change_percent = float(quote.get("10. change percent", "0").strip('%'))
            
            return f"""Stock Price Information for {symbol}:
            Current Price: ₹{price:.2f}
            Change: ₹{change:.2f} ({change_percent:.2f}%)
            
            Note: Prices are delayed by 15 minutes."""
        return f"Unable to fetch price for {symbol}. Please check the symbol and try again."
    except Exception as e:
        return f"Error fetching stock price: {str(e)}"

@tool
def crypto_price_fetcher(query: str) -> str:
    """Fetch cryptocurrency prices.
    Query format: 'crypto: CRYPTO_SYMBOL'
    """
    try:
        crypto = query.split(':')[1].strip()
        #ba9a09b4-084d-44c9-8480-ef6779e413e7
        # Using CoinGecko API (free, no API key required)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto.lower()}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        
        if crypto.lower() in data:
            price = data[crypto.lower()]["usd"]
            return f"Current price for {crypto}: ${price:,.2f}"
        return f"Unable to fetch price for {crypto}. Please check the symbol."
    except Exception as e:
        return f"Error fetching crypto price: {str(e)}"

@tool
def currency_converter(query: str) -> str:
    """Convert between currencies.
    Query format: 'amount: NUMBER, from_currency: CURRENCY, to_currency: CURRENCY'
    """
    try:
        parts = [p.strip() for p in query.split(',')]
        amount = float(parts[0].split(':')[1])
        from_curr = parts[1].split(':')[1].strip()
        to_curr = parts[2].split(':')[1].strip()
        
        # Using ExchangeRate-API (free tier available)
        API_KEY = "bbbc65db3de68e646ed8eb3b"
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{from_curr}/{to_curr}"
        response = requests.get(url)
        data = response.json()
        
        if data["result"] == "success":
            rate = data["conversion_rate"]
            converted = amount * rate
            return f"{amount} {from_curr} = {converted:.2f} {to_curr}"
        return "Unable to fetch conversion rate"
    except Exception as e:
        return f"Error converting currency: {str(e)}"

@tool
def savings_plan_calculator(query: str) -> str:
    """Calculate a savings plan based on income and expenses.
    Query format: 'monthly_income: NUMBER, monthly_expenses: NUMBER'
    """
    try:
        # Clean the input by removing commas, ₹ symbol, and extra spaces
        query = query.replace('₹', '').replace(',', '').strip()
        
        # Extract numbers from the query using more robust parsing
        income_part = query.split('monthly_expenses')[0]  # Get the first part containing income
        expense_part = query.split('monthly_expenses:')[1] if 'monthly_expenses:' in query else "0"
        
        # Extract the numeric values using string manipulation
        monthly_income = float(''.join(filter(str.isdigit, income_part)))
        monthly_expenses = float(''.join(filter(str.isdigit, expense_part)))
        
        # Validate the extracted values
        if monthly_income <= 0 or monthly_expenses < 0:
            return "Error: Please provide valid positive numbers for income and expenses."
        
        # Calculate disposable income
        disposable_income = monthly_income - monthly_expenses
        
        # Calculate recommended allocations
        emergency_fund = disposable_income * 0.30
        investments = disposable_income * 0.50
        discretionary = disposable_income * 0.20
        
        # Calculate emergency fund target (6 months of expenses)
        emergency_fund_target = monthly_expenses * 6
        months_to_emergency_fund = emergency_fund_target / emergency_fund if emergency_fund > 0 else float('inf')
        
        return f"""Personalized Savings Plan:
        Monthly Analysis:
        ├── Income: ₹{monthly_income:,.2f}
        ├── Expenses: ₹{monthly_expenses:,.2f}
        └── Disposable Income: ₹{disposable_income:,.2f}

        Recommended Monthly Allocation:
        ├── Emergency Fund: ₹{emergency_fund:,.2f}
        ├── Investments: ₹{investments:,.2f}
        └── Discretionary: ₹{discretionary:,.2f}

        Emergency Fund Goals:
        ├── Target: ₹{emergency_fund_target:,.2f} (6 months of expenses)
        └── Months to reach target: {months_to_emergency_fund:.1f}

        Investment Suggestions:
        ├── Equity Mutual Funds: 50%
        ├── Debt Funds: 40%
        └── Gold: 10%

        Additional Recommendations:
        ├── Set up automatic transfers for savings
        ├── Review and reduce unnecessary expenses
        ├── Consider tax-saving investments
        └── Review plan quarterly"""
    except Exception as e:
        # Provide a more helpful error message
        return f"""Error calculating savings plan: {str(e)}
        Please ensure input format is 'monthly_income: NUMBER, monthly_expenses: NUMBER'
        Example: monthly_income: 100000, monthly_expenses: 50000"""

@tool
def tax_calculator(query: str) -> str:
    """Calculate tax liability.
    Query format: 'annual_income: NUMBER, country: COUNTRY'
    """
    parts = [p.strip() for p in query.split(',')]
    income = float(parts[0].split(':')[1])
    country = parts[1].split(':')[1].strip()
    
    # Simplified Indian tax calculation for demo
    if country.lower() == 'india':
        if income <= 500000:
            tax = 0
        elif income <= 1000000:
            tax = (income - 500000) * 0.2
        else:
            tax = 100000 + (income - 1000000) * 0.3
        
        return f"""Estimated tax liability for annual income of ₹{income:,.2f}:
        Tax Amount: ₹{tax:,.2f}
        Effective Tax Rate: {(tax/income)*100:.1f}%"""
    return "Tax calculation is currently only supported for India"

@tool
def loan_eligibility_checker(query: str) -> str:
    """Check loan eligibility.
    Query format: 'monthly_income: NUMBER, existing_emis: NUMBER, credit_score: NUMBER'
    """
    parts = [p.strip() for p in query.split(',')]
    monthly_income = float(parts[0].split(':')[1])
    existing_emis = float(parts[1].split(':')[1])
    credit_score = float(parts[2].split(':')[1])
    
    # Calculate eligibility
    total_obligations = existing_emis
    max_emi = monthly_income * 0.5  # 50% of income
    available_emi = max_emi - total_obligations
    
    if credit_score >= 700:
        multiplier = 60  # 5 years
    else:
        multiplier = 36  # 3 years
    
    max_loan = available_emi * multiplier
    
    return f"""Loan Eligibility Analysis:
    Monthly Income: ₹{monthly_income:,.2f}
    Current EMIs: ₹{existing_emis:,.2f}
    Credit Score: {credit_score}
    
    Results:
    Maximum EMI Capacity: ₹{max_emi:,.2f}
    Available EMI Capacity: ₹{available_emi:,.2f}
    Maximum Loan Amount: ₹{max_loan:,.2f}
    Loan Term: {multiplier} months"""

@tool
def retirement_planner(query: str) -> str:
    """Plan retirement savings.
    Query format: 'age: NUMBER, monthly_income: NUMBER, retirement_age: NUMBER'
    """
    parts = [p.strip() for p in query.split(',')]
    current_age = int(parts[0].split(':')[1])
    monthly_income = float(parts[1].split(':')[1])
    retirement_age = int(parts[2].split(':')[1])
    
    years_to_retirement = retirement_age - current_age
    monthly_savings_needed = (monthly_income * 0.6) * 12 * 25 / (years_to_retirement * 12)
    
    return f"""Retirement Planning Analysis:
    Current Age: {current_age}
    Years until retirement: {years_to_retirement}
    Monthly Income: ₹{monthly_income:,.2f}
    
    Recommendations:
    Monthly Savings Needed: ₹{monthly_savings_needed:,.2f}
    Target Retirement Corpus: ₹{monthly_income * 0.6 * 12 * 25:,.2f}
    (Assuming 60% of current income needed post-retirement and 25 years post-retirement)"""

@tool
def market_news_fetcher(query: str = "") -> str:
    """Fetch latest market news headlines."""
    try:
        # Using News API (requires free API key)
        API_KEY = "88efff8404f844f2802a7e5893346868"
        url = f"https://newsapi.org/v2/top-headlines?country=us&category=business&apiKey={API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data["status"] == "ok":
            news = [article["title"] for article in data["articles"][:4]]
            return "\n".join([f"📰 {item}" for item in news])
        return "Unable to fetch market news"
    except Exception as e:
        return f"Error fetching market news: {str(e)}"

@tool
def investment_risk_assessor(query: str) -> str:
    """Assess investment risks.
    Query format: 'amount: NUMBER, risk_profile: PROFILE'
    Profiles can be: conservative, moderate, aggressive
    """
    try:
        parts = [p.strip() for p in query.split(',')]
        amount = float(parts[0].split(':')[1])
        risk_profile = parts[1].split(':')[1].strip().lower()
        
        # Risk profile based allocations
        risk_profiles = {
            'conservative': {
                'stocks': 30,
                'bonds': 50,
                'gold': 10,
                'cash': 10,
                'risk_level': 'Low',
                'expected_return': '8-10%'
            },
            'moderate': {
                'stocks': 50,
                'bonds': 30,
                'gold': 10,
                'cash': 10,
                'risk_level': 'Medium',
                'expected_return': '10-12%'
            },
            'aggressive': {
                'stocks': 70,
                'bonds': 20,
                'gold': 5,
                'cash': 5,
                'risk_level': 'High',
                'expected_return': '12-15%'
            }
        }
        
        if risk_profile not in risk_profiles:
            return "Risk profile not recognized. Please choose from: conservative, moderate, aggressive"
        
        profile = risk_profiles[risk_profile]
        
        return f"""Investment Risk Assessment:

        Investment Details:
        ├── Amount: ₹{amount:,.2f}
        ├── Risk Profile: {risk_profile.title()}
        └── Risk Level: {profile['risk_level']}

        Recommended Asset Allocation:
        ├── Stocks: ₹{(amount * profile['stocks']/100):,.2f} ({profile['stocks']}%)
        ├── Bonds: ₹{(amount * profile['bonds']/100):,.2f} ({profile['bonds']}%)
        ├── Gold: ₹{(amount * profile['gold']/100):,.2f} ({profile['gold']}%)
        └── Cash: ₹{(amount * profile['cash']/100):,.2f} ({profile['cash']}%)

        Expected Return: {profile['expected_return']} annually

        Investment Strategy:
        ├── Diversification across multiple asset classes
        ├── Regular portfolio rebalancing
        ├── Systematic investment approach
        └── Regular monitoring and review

        Note: Past performance does not guarantee future returns."""
    except Exception as e:
        return f"Error assessing investment risk: {str(e)}"

@tool
def blue_chip_stocks_fetcher(query: str = "") -> str:
    """Fetch list of major Indian blue-chip stocks"""
    try:
        # List of major Indian blue-chip stocks (NSE)
        blue_chips = [
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries"},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services"},
            {"symbol": "HDFCBANK.NS", "name": "HDFC Bank"},
            {"symbol": "INFY.NS", "name": "Infosys"},
            {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever"},
            {"symbol": "ICICIBANK.NS", "name": "ICICI Bank"},
            {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel"},
            {"symbol": "ITC.NS", "name": "ITC"},
            {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank"},
            {"symbol": "LT.NS", "name": "Larsen & Toubro"}
        ]
        
        result = "Top Indian Blue-Chip Stocks:\n\n"
        for stock in blue_chips:
            # Fetch current price using stock_price_fetcher
            price_info = stock_price_fetcher(f"symbol: {stock['symbol']}")
            result += f"📈 {stock['name']} ({stock['symbol']})\n"
            result += f"{price_info}\n\n"
            
        return result
    except Exception as e:
        return f"Error fetching blue-chip stocks: {str(e)}"
