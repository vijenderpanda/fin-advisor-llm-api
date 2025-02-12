from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from typing import List, Dict, Any
import json
import logging
from sqlalchemy import create_engine
from contextlib import contextmanager
from sqlalchemy.pool import QueuePool

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
postgres_url = "postgresql+psycopg://neondb_owner:npg_y8IjUwmbv0sW@ep-flat-glade-a4m83cg4-pooler.us-east-1.aws.neon.tech/neondb"
engine = create_engine(
    postgres_url,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800  # Recycle connections after 30 minutes
)

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    try:
        connection = engine.connect()
        yield connection
    finally:
        connection.close()

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
        
        # Updated prompt with concrete parameter examples
        self.planner_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a pragmatic financial advisor combining Warren Buffett's wisdom with modern financial planning principles. Your goal is to create realistic, achievable financial plans that balance growth with security.

            CRITICAL: You MUST ALWAYS respond with a valid JSON object following the exact structure below. DO NOT include any text outside the JSON structure.
            
            **Input:**
            - **User Inputs**: {question}
            - Chat History: {history}

            {{
                "plan": [
                    {{
                        "step": 1,
                        "tool": "savings_plan_calculator",
                        "description": "Calculate emergency fund and monthly savings targets",
                        "parameters": {{
                            "monthly_income": 100000,
                            "monthly_expenses": 50000
                        }}
                    }},
                    {{
                        "step": 2,
                        "tool": "investment_risk_assessor",
                        "description": "Assess risk profile and suggest allocation",
                        "parameters": {{
                            "amount": 5000000,
                            "risk_profile": "moderate"
                        }}
                    }}
                ],
                "status": "READY"
            }}

            Available Tools and Required Parameters:
            1. savings_plan_calculator:
               - monthly_income: NUMBER (e.g., 100000)
               - monthly_expenses: NUMBER (e.g., 50000)
            2. investment_risk_assessor:
               - amount: NUMBER (e.g., 1000000)
               - risk_profile: STRING (conservative/moderate/aggressive)
            3. loan_eligibility_checker:
               - monthly_income: NUMBER
               - existing_emis: NUMBER
               - credit_score: NUMBER
            4. tax_calculator:
               - annual_income: NUMBER
               - country: STRING
            5. retirement_planner:
               - age: NUMBER
               - monthly_income: NUMBER
               - retirement_age: NUMBER

            Guidelines:
            1. Use EXACT parameter names as shown above
            2. Always provide numeric values without commas or currency symbols
            3. Use lowercase for risk profiles and text inputs
            4. Include 2-4 concrete steps using available tools"""),
            MessagesPlaceholder(variable_name="history"),
        ])
        
        # Initialize the executor prompt
        self.executor_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a financial execution AI that carries out specific financial plans.
             **Input:**
            - **Plan**: {plan}
            - Chat History: {history}
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
                connection=engine
            ),
            input_messages_key="question",
            history_messages_key="history"
        )

        self.executor_chain_with_history = RunnableWithMessageHistory(
            self.executor_chain,
            lambda session_id: SQLChatMessageHistory(
                session_id=session_id,
                connection=engine
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
                        if tool_name == "savings_plan_calculator":
                            # Ensure parameters are numbers and properly formatted
                            monthly_income = float(parameters.get('monthly_income', 0))
                            monthly_expenses = float(parameters.get('monthly_expenses', 0))
                            query = f"monthly_income: {monthly_income}, monthly_expenses: {monthly_expenses}"
                            result = tool.invoke(query)
                        elif tool_name == "investment_risk_assessor":
                            # Handle both 'amount' and 'investment_amount' parameters
                            amount = float(parameters.get('investment_amount', parameters.get('amount', 100000)))
                            risk_profile = str(parameters.get('risk_profile', 'moderate')).lower()
                            query = f"amount: {amount}, risk_profile: {risk_profile}"
                            result = tool.invoke(query)
                        elif tool_name == "loan_eligibility_checker":
                            query = f"monthly_income: {parameters.get('monthly_income')}, existing_emis: {parameters.get('existing_emis', 0)}, credit_score: {parameters.get('credit_score', 750)}"
                            result = tool.invoke(query)
                        elif tool_name == "tax_calculator":
                            query = f"annual_income: {parameters.get('annual_income')}, country: {parameters.get('country', 'india')}"
                            result = tool.invoke(query)
                        elif tool_name == "retirement_planner":
                            query = f"age: {parameters.get('current_age', 30)}, monthly_income: {parameters.get('monthly_income', 0)}, retirement_age: {parameters.get('retirement_age', 60)}"
                            result = tool.invoke(query)
                        elif tool_name == "stock_price_fetcher":
                            query = f"symbol: {parameters.get('symbol', '')}"
                            result = tool.invoke(query)
                        elif tool_name == "crypto_price_fetcher":
                            query = f"crypto: {parameters.get('symbol', parameters.get('crypto', 'bitcoin'))}"
                            result = tool.invoke(query)
                        elif tool_name == "market_news_fetcher":
                            result = tool.invoke("")
                        else:
                            result = tool.invoke(str(parameters))
                            
                        results.append({
                            "step": step["step"],
                            "output": result,
                            "status": "SUCCESS"
                        })
                    except ValueError as ve:
                        logger.error(f"Parameter conversion error for {tool_name}: {str(ve)}")
                        results.append({
                            "step": step["step"],
                            "output": f"Error: Invalid parameter format in {tool_name}. Please provide numeric values without commas or currency symbols.",
                            "status": "FAILED"
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