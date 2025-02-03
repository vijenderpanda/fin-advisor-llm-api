from langchain.tools import tool
import requests
import random
import json


@tool
def stock_price_fetcher(query: str) -> str:
    """Fetch real-time stock prices.
    Query format: 'symbol: STOCK_SYMBOL'
    """
    symbol = query.split(':')[1].strip()
    # Simulated price for demo
    price = random.uniform(100, 1000)
    return f"Current stock price for {symbol}: ${price:.2f}"

@tool
def crypto_price_fetcher(query: str) -> str:
    """Fetch cryptocurrency prices.
    Query format: 'crypto: CRYPTO_SYMBOL'
    """
    crypto = query.split(':')[1].strip()
    # Simulated price for demo
    price = random.uniform(20000, 60000)
    return f"Current price for {crypto}: ${price:.2f}"

@tool
def currency_converter(query: str) -> str:
    """Convert between currencies.
    Query format: 'amount: NUMBER, from_currency: CURRENCY, to_currency: CURRENCY'
    """
    parts = [p.strip() for p in query.split(',')]
    amount = float(parts[0].split(':')[1])
    from_curr = parts[1].split(':')[1].strip()
    to_curr = parts[2].split(':')[1].strip()
    # Simulated conversion rate for demo
    rate = 83.0 if (from_curr == "USD" and to_curr == "INR") else 1/83.0
    converted = amount * rate
    return f"{amount} {from_curr} = {converted:.2f} {to_curr}"

@tool
def savings_plan_calculator(query: str) -> str:
    """Calculate a savings plan based on income and expenses.
    Query format: 'monthly_income: NUMBER, monthly_expenses: NUMBER'
    """
    parts = [p.strip() for p in query.split(',')]
    monthly_income = float(parts[0].split(':')[1])
    monthly_expenses = float(parts[1].split(':')[1])
    
    disposable_income = monthly_income - monthly_expenses
    emergency_fund = disposable_income * 0.3
    investments = disposable_income * 0.5
    discretionary = disposable_income * 0.2
    
    return f"""Based on your monthly income of ₹{monthly_income:,.2f} and expenses of ₹{monthly_expenses:,.2f}:
    Disposable Income: ₹{disposable_income:,.2f}
    Recommended Monthly Allocation:
    1. Emergency Fund: ₹{emergency_fund:,.2f} (30%)
    2. Investments: ₹{investments:,.2f} (50%)
    3. Discretionary Spending: ₹{discretionary:,.2f} (20%)"""

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
    # Simulated news for demo
    news = [
        "Federal Reserve Maintains Interest Rates",
        "Global Markets Show Strong Recovery",
        "Tech Stocks Lead Market Rally",
        "Oil Prices Stabilize Amid Global Demand"
    ]
    return "\n".join([f"📰 {item}" for item in news])

@tool
def investment_risk_assessor(query: str) -> str:
    """Assess investment risks.
    Query format: 'amount: NUMBER, investment_type: TYPE'
    """
    parts = [p.strip() for p in query.split(',')]
    amount = float(parts[0].split(':')[1])
    investment_type = parts[1].split(':')[1].strip().lower()
    
    risk_levels = {
        'stocks': 'High',
        'bonds': 'Medium',
        'tech stocks': 'Very High',
        'mutual funds': 'Medium',
        'crypto': 'Very High'
    }
    
    risk_level = risk_levels.get(investment_type, 'Unknown')
    
    return f"""Investment Risk Assessment:
    Amount: ₹{amount:,.2f}
    Investment Type: {investment_type}
    Risk Level: {risk_level}
    
    Recommendations:
    - Consider diversifying across multiple asset classes
    - Start with a smaller position size
    - Monitor market conditions regularly"""
