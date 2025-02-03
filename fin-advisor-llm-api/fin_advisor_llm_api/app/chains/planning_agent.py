from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from typing import List, Dict, Any
import json
import logging

# Import existing tools
from fin_advisor_llm_api.app.tools.tool import (
    stock_price_fetcher,
    crypto_price_fetcher,
    currency_converter,
    savings_plan_calculator,
    tax_calculator,
    loan_eligibility_checker,
    retirement_planner,
    market_news_fetcher,
    investment_risk_assessor
)

logger = logging.getLogger(__name__)

# Add this near your imports
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Database configuration
postgres_memory_url = "postgresql+psycopg://neondb_owner:npg_y8IjUwmbv0sW@ep-flat-glade-a4m83cg4-pooler.us-east-1.aws.neon.tech/neondb"


class PlanningAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.tools = [
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
        
        # Updated prompt with stronger JSON enforcement
        self.planner_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a pragmatic financial advisor combining Warren Buffett's wisdom with modern financial planning principles. Your goal is to create realistic, achievable financial plans that balance growth with security.

            CRITICAL: You MUST ALWAYS respond with a valid JSON object following the exact structure below. DO NOT include any text outside the JSON structure.

            {{
                "plan": [
                    {{
                        "step": 1,
                        "tool": "savings_plan_calculator",
                        "description": "Calculate emergency fund and monthly savings targets",
                        "parameters": {{
                            "monthly_income": <income>,
                            "monthly_expenses": <expenses>
                        }}
                    }},
                    {{
                        "step": 2,
                        "tool": "investment_risk_assessor",
                        "description": "Assess risk profile and suggest allocation",
                        "parameters": {{
                            "investment_amount": <amount>,
                            "risk_profile": "<risk_level>"
                        }}
                    }}
                    // Additional steps as needed
                ],
                "status": "READY"
            }}

            Available Tools:
            1. savings_plan_calculator: Design savings plan
            2. tax_calculator: Tax optimization
            3. loan_eligibility_checker: Borrowing capacity
            4. retirement_planner: Retirement planning
            5. investment_risk_assessor: Risk analysis
            6. stock_price_fetcher: Stock research
            7. market_news_fetcher: Market updates

            Guidelines for Plan Creation:
            1. ALWAYS use the exact JSON structure shown above
            2. Include 2-4 concrete steps using available tools
            3. Each step must have valid parameters for the tool
            4. Use realistic amounts based on provided income
            5. Focus on immediate actionable steps

            If you need more information:
            1. Set "status": "NEED_INFO"
            2. Include specific question in "missing_info" field
            
            Example Valid Response:
            {{
                "plan": [
                    {{
                        "step": 1,
                        "tool": "savings_plan_calculator",
                        "description": "Calculate monthly savings allocation",
                        "parameters": {{
                            "monthly_income": 200000,
                            "monthly_expenses": 70000
                        }}
                    }}
                ],
                "status": "READY"
            }}

            Remember: ONLY output valid JSON. No additional text or explanations outside the JSON structure."""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])
        
        # Initialize the executor prompt
        self.executor_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial execution AI that carries out specific financial plans.
            Execute each step in the plan and return results in this exact JSON format:
            {{
                "results": [
                    {{
                        "step": 1,
                        "output": "result of the tool execution",
                        "status": "SUCCESS"
                    }}
                ],
                "final_advice": "summary of recommendations"
            }}"""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{plan}")
        ])

        # Create planner chain
        self.planner_chain = (
            self.planner_prompt 
            | self.llm 
            | JsonOutputParser()
        )

        # Create executor chain
        self.executor_chain = (
            self.executor_prompt 
            | self.llm 
            | JsonOutputParser()
        )

        # Add message history
        self.planner_chain_with_history = RunnableWithMessageHistory(
            self.planner_chain,
            lambda session_id: SQLChatMessageHistory(
                session_id=session_id,
                connection_string=postgres_memory_url
            ),
            input_messages_key="question",
            history_messages_key="history"
        )

        self.executor_chain_with_history = RunnableWithMessageHistory(
            self.executor_chain,
            lambda session_id: SQLChatMessageHistory(
                session_id=session_id,
                connection_string=postgres_memory_url
            ),
            input_messages_key="plan",
            history_messages_key="history"
        )

    def create_plan(self, user_input: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a plan based on user input"""
        try:
            # Get response using chain
            response = self.planner_chain_with_history.invoke(
                {"question": user_input},
                config=config
            )
            
            # Log the raw content for debugging
            logger.debug(f"Raw chain response: {response}")
            
            # Validate the required structure
            if "plan" not in response or "status" not in response:
                raise ValueError("Response missing required keys: 'plan' and/or 'status'")
            
            return response
                
        except Exception as e:
            logger.error(f"Error in create_plan: {str(e)}")
            return {
                "error": "Failed to create financial plan",
                "details": str(e)
            }

    def execute_plan(self, plan: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a generated plan"""
        try:
            results = []
            
            for step in plan.get("plan", []):
                tool_name = step.get("tool")
                parameters = step.get("parameters", {})
                
                # Find the appropriate tool
                tool = next((t for t in self.tools if t.name == tool_name), None)
                
                if tool:
                    try:
                        # Format parameters into a query string based on the tool
                        if tool_name == "loan_eligibility_checker":
                            query = f"monthly_income: {parameters.get('monthly_income')}, existing_emis: {parameters.get('existing_emis')}, credit_score: {parameters.get('credit_score')}"
                            result = tool(query)
                        elif tool_name == "savings_plan_calculator":
                            query = f"monthly_income: {parameters.get('monthly_income')}, monthly_expenses: {parameters.get('monthly_expenses')}"
                            result = tool(query)
                        elif tool_name == "tax_calculator":
                            query = f"annual_income: {parameters.get('annual_income')}, country: {parameters.get('country')}"
                            result = tool(query)
                        elif tool_name == "retirement_planner":
                            # Proper type casting for retirement planner parameters
                            try:
                                current_age = int(str(parameters.get('current_age')).strip())
                                retirement_age = int(str(parameters.get('retirement_age')).strip())
                                monthly_income = float(str(parameters.get('monthly_income', parameters.get('monthly_expenses', 0))).strip())
                                
                                query = f"age: {current_age}, monthly_income: {monthly_income}, retirement_age: {retirement_age}"
                                result = tool(query)
                            except (ValueError, TypeError) as e:
                                logger.error(f"Parameter type casting error in retirement_planner: {str(e)}")
                                raise ValueError(f"Invalid parameters for retirement planning: {str(e)}")
                        elif tool_name == "currency_converter":
                            query = f"amount: {parameters.get('amount')}, from_currency: {parameters.get('from_currency')}, to_currency: {parameters.get('to_currency')}"
                            result = tool(query)
                        elif tool_name == "stock_price_fetcher":
                            query = f"symbol: {parameters.get('symbol')}"
                            result = tool(query)
                        elif tool_name == "crypto_price_fetcher":
                            crypto_symbol = parameters.get('symbol', parameters.get('crypto', 'BTC'))
                            query = f"crypto: {crypto_symbol}"
                            result = tool(query)
                        elif tool_name == "investment_risk_assessor":
                            # Calculate realistic investment amount based on income and parameters
                            try:
                                # Get monthly income if available
                                monthly_income = float(str(parameters.get('monthly_income', 0)).strip())
                                
                                # Calculate investment amount based on different sources
                                if parameters.get('investment_amount'):
                                    amount = float(str(parameters.get('investment_amount')).strip())
                                elif parameters.get('amount'):
                                    amount = float(str(parameters.get('amount')).strip())
                                elif monthly_income > 0:
                                    # If no amount specified but we have income, calculate 6 months of savings
                                    amount = monthly_income * 6
                                else:
                                    # Minimum realistic investment amount
                                    amount = 100000  # Default to 1 lakh INR as minimum
                                
                                # Get risk profile and map to investment type
                                risk_profile = str(parameters.get('risk_profile', 'moderate')).strip().lower()
                                
                                # Map risk profile to investment type and allocation
                                risk_map = {
                                    'conservative': {
                                        'type': 'fixed_income',
                                        'allocation': 'Fixed Income: 60%, Large Cap: 30%, Mid Cap: 10%'
                                    },
                                    'moderate': {
                                        'type': 'balanced',
                                        'allocation': 'Large Cap: 40%, Mid Cap: 30%, Fixed Income: 30%'
                                    },
                                    'aggressive': {
                                        'type': 'growth',
                                        'allocation': 'Mid Cap: 40%, Small Cap: 30%, Large Cap: 30%'
                                    }
                                }
                                
                                investment_details = risk_map.get(risk_profile, risk_map['moderate'])
                                investment_type = investment_details['type']
                                
                                query = f"amount: {amount}, investment_type: {investment_type}"
                                result = tool(query)
                                
                                # Enhance the result with allocation details
                                result = result.replace(
                                    "Recommendations:",
                                    f"Recommended Allocation:\n    {investment_details['allocation']}\n\n    Recommendations:"
                                )
                                
                            except (ValueError, TypeError) as e:
                                logger.error(f"Parameter type casting error in investment_risk_assessor: {str(e)}")
                                raise ValueError(f"Invalid parameters for risk assessment: {str(e)}")
                        elif tool_name == "market_news_fetcher":
                            result = tool("")  # No parameters needed
                        else:
                            # For any other tools, pass the query as is
                            result = tool(parameters.get("query", ""))
                            
                        results.append({
                            "step": step["step"],
                            "output": result,
                            "status": "SUCCESS"
                        })
                    except Exception as e:
                        logger.error(f"Tool execution error for {tool_name}: {str(e)}")
                        results.append({
                            "step": step["step"],
                            "output": f"Error in {tool_name}: {str(e)}",
                            "status": "FAILED"
                        })
                else:
                    results.append({
                        "step": step["step"],
                        "output": f"Tool {tool_name} not found",
                        "status": "FAILED"
                    })
            
            # Generate final advice using executor chain
            executor_response = self.executor_chain_with_history.invoke(
                {"plan": json.dumps({"results": results})},
                config=config
            )
            
            return {
                "results": results,
                "final_advice": executor_response.get("final_advice", "")
            }
            
        except Exception as e:
            logger.error(f"Error in execute_plan: {str(e)}")
            return {
                "error": "Failed to execute plan",
                "details": str(e)
            }

    def run(self, user_input: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the full planning and execution pipeline"""
        try:
            # Generate plan
            plan = self.create_plan(user_input, config)
            
            if "error" in plan:
                return plan
                
            if plan.get("status") != "READY":
                return {
                    "status": "INCOMPLETE",
                    "message": "Unable to create a complete plan. Please provide more information."
                }
                
            # Execute plan
            results = self.execute_plan(plan, config)
            
            if "error" in results:
                return results
                
            return {
                "status": "SUCCESS",
                "plan": plan,
                "execution_results": results
            }
            
        except Exception as e:
            logger.error(f"Error in run: {str(e)}")
            return {
                "status": "ERROR",
                "error": "Failed to process request",
                "details": str(e)
            } 