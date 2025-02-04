from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from typing import Dict, Any
import logging
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
from langchain_community.chat_message_histories import SQLChatMessageHistory
import datetime
import json
import re
import traceback

logger = logging.getLogger(__name__)

class FinancialMultiAgent:
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
        self.postgres_memory_url = "postgresql://neondb_owner:npg_y8IjUwmbv0sW@ep-flat-glade-a4m83cg4-pooler.us-east-1.aws.neon.tech/neondb"

    def get_client_history(self, session_id: str) -> Dict:
        """Retrieve client information from chat history"""
        chat_history = SQLChatMessageHistory(
            connection_string=self.postgres_memory_url,
            session_id=session_id
        )
        
        # Analyze chat history to extract client information
        messages = chat_history.messages
        # Initialize default profile
        client_profile = {
            "risk_tolerance": "moderate",  # Default value
            "investment_horizon": "medium_term",
            "extracted_from_history": False
        }
        
        return client_profile

    def create_agents(self):
        # Information Gathering Agent
        info_gatherer = Agent(
            role="Information Gathering Specialist",
            goal="Gather and analyze client information and requirements",
            backstory="""Expert in understanding client needs and extracting key information 
            from conversations. Skilled at identifying missing critical details.""",
            tools=[],
            verbose=True
        )
        
        # Market Analysis Agent
        market_analyst = Agent(
            role="Market Research Analyst",
            goal="Analyze current market conditions and investment opportunities",
            backstory="""Senior market analyst with expertise in identifying market trends 
            and investment opportunities across different asset classes.""",
            tools=[market_news_fetcher, stock_price_fetcher, crypto_price_fetcher],
            verbose=True
        )
        
        # Investment Strategy Agent
        strategist = Agent(
            role="Investment Strategist",
            goal="Develop personalized investment strategies",
            backstory="""Experienced investment strategist skilled at creating 
            tailored investment plans based on market conditions and client profiles.""",
            tools=[investment_risk_assessor, savings_plan_calculator],
            verbose=True
        )
        
        return [info_gatherer, market_analyst, strategist]

    def create_tasks(self, agents: list, user_input: str, session_id: str):
        info_gatherer, market_analyst, strategist = agents
        
        # Define expected output templates
        info_gatherer_output = {
            "investment_amount": 5000000,
            "goals": ["balanced portfolio", "long-term growth"],
            "preferences": {
                "risk_level": "moderate",
                "investment_horizon": "long-term",
                "constraints": ["monthly dividend income"]
            },
            "risk_tolerance": "medium",
            "time_horizon": "long term"
        }

        market_analyst_output = {
            "market_conditions": {
                "overall_sentiment": "positive/negative/neutral",
                "key_indicators": ["indicator1", "indicator2"],
                "market_trends": ["trend1", "trend2"]
            },
            "opportunities": ["opportunity1", "opportunity2"],
            "risks": ["risk1", "risk2"],
            "asset_class_analysis": {
                "equities": "detailed analysis",
                "fixed_income": "detailed analysis",
                "commodities": "detailed analysis",
                "crypto": "detailed analysis"
            }
        }

        strategist_output = {
            "asset_allocation": {
                "equities": "50%",
                "fixed_income": "30%",
                "alternatives": "15%",
                "cash": "5%"
            },
            "investment_recommendations": [
                {
                    "asset_type": "Technology Stocks",
                    "allocation": "20%",
                    "rationale": "Strong growth potential"
                }
            ],
            "risk_management": {
                "diversification_strategy": "strategy details",
                "risk_mitigation_measures": ["measure1", "measure2"],
                "monitoring_plan": "monitoring details"
            },
            "action_steps": [
                {
                    "step": 1,
                    "action": "action description",
                    "timeline": "timeline details"
                }
            ]
        }
        
        tasks = [
            Task(
                description=f"""
                Analyze user query and chat history to understand:
                1. Investment amount and goals
                2. Any mentioned preferences or constraints
                3. Risk tolerance indicators
                4. Time horizon preferences
                
                User Query: {user_input}
                
                IMPORTANT: Your response must be in valid JSON format.
                Start your final answer with '## Final Answer:' followed by a JSON object matching this structure:
                {json.dumps(info_gatherer_output, indent=2)}
                """,
                agent=info_gatherer,
                expected_output=json.dumps(info_gatherer_output)
            ),
            Task(
                description=f"""
                Based on the investment amount and gathered information:
                1. Analyze current market conditions
                2. Identify suitable investment opportunities
                3. Consider multiple asset classes
                4. Evaluate market risks and opportunities
                
                IMPORTANT: Your response must be in valid JSON format.
                Start your final answer with '## Final Answer:' followed by a JSON object matching this structure:
                {json.dumps(market_analyst_output, indent=2)}
                """,
                agent=market_analyst,
                expected_output=json.dumps(market_analyst_output)
            ),
            Task(
                description=f"""
                Create a comprehensive investment strategy:
                1. Asset allocation recommendations
                2. Specific investment suggestions
                3. Risk management approach
                4. Implementation steps
                
                IMPORTANT: Your response must be in valid JSON format.
                Start your final answer with '## Final Answer:' followed by a JSON object matching this structure:
                {json.dumps(strategist_output, indent=2)}
                """,
                agent=strategist,
                expected_output=json.dumps(strategist_output)
            )
        ]
        return tasks

    async def run_analysis(
        self,
        user_input: str,
        session_id: str,
        config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        try:
            agents = self.create_agents()
            tasks = self.create_tasks(agents, user_input, session_id)
            
            crew = Crew(
                agents=agents,
                tasks=tasks,
                process=Process.sequential,
                verbose=True
            )
            
            # Execute the crew and store result
            start_time = datetime.datetime.now()
            result = crew.kickoff()
            end_time = datetime.datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Debug logging
            logger.info("=== CrewAI Execution Result ===")
            logger.info(str(result))
            logger.info("==============================")
            
            # Try to parse the result as JSON
            try:
                if isinstance(result, str):
                    if result.startswith('{'):
                        final_result = json.loads(result)
                    else:
                        raise json.JSONDecodeError("Not a JSON string", result, 0)
                else:
                    final_result = result
                
                logger.info("Successfully parsed result as JSON")
                
                # Create detailed workflow summary
                workflow_details = {
                    "agents": [
                        {
                            "name": "Information Gathering Specialist",
                            "role": "Info Gatherer",
                            "description": "Analyzes user queries and requirements",
                            "tools_used": ["savings_plan_calculator", "investment_risk_assessor"],
                            "responsibility": "Initial analysis of investment requirements and constraints"
                        },
                        {
                            "name": "Market Research Analyst",
                            "role": "Market Analyst",
                            "description": "Analyzes market conditions and opportunities",
                            "tools_used": ["market_news_fetcher", "stock_price_fetcher", "crypto_price_fetcher"],
                            "responsibility": "Market analysis and opportunity identification"
                        },
                        {
                            "name": "Investment Strategist",
                            "role": "Strategist",
                            "description": "Creates comprehensive investment strategies",
                            "tools_used": ["investment_risk_assessor", "savings_plan_calculator"],
                            "responsibility": "Final strategy formulation and recommendations"
                        }
                    ],
                    "workflow_steps": [
                        {
                            "step": 1,
                            "agent": "Info Gatherer",
                            "action": "Information gathering and requirement analysis",
                            "tools_used": ["savings_plan_calculator", "investment_risk_assessor"],
                            "output_type": "User profile and requirements"
                        },
                        {
                            "step": 2,
                            "agent": "Market Analyst",
                            "action": "Market research and analysis",
                            "tools_used": ["market_news_fetcher", "stock_price_fetcher"],
                            "output_type": "Market analysis and opportunities"
                        },
                        {
                            "step": 3,
                            "agent": "Strategist",
                            "action": "Strategy formulation",
                            "tools_used": ["investment_risk_assessor"],
                            "output_type": "Investment strategy and recommendations"
                        }
                    ]
                }
                
                # Create enhanced response
                response = {
                    "session_id": session_id,
                    "query": user_input,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "workflow_summary": {
                        "tasks": [
                            {
                                "name": "Investment Strategy",
                                "description": "Create a comprehensive investment strategy...",
                                "agent": "Strategist",
                                "tool_interactions": [],
                                "final_answer": final_result
                            }
                        ]
                    },
                    "execution_summary": {
                        "total_agents": len(agents),
                        "total_tasks": len(tasks),
                        "execution_flow": "sequential",
                        "completion_status": "success",
                        "execution_time": f"{execution_time:.2f} seconds",
                        "start_time": start_time.isoformat(),
                        "end_time": end_time.isoformat()
                    },
                    "workflow_details": workflow_details,
                    "raw_output": str(result)  # Include raw output for reference
                }
                
                return response
                
            except json.JSONDecodeError:
                logger.info("Result is not JSON, trying section extraction")
                result_str = str(result)
                
                # Only extract sections if we find the agent markers
                if "# Agent:" in result_str:
                    def extract_agent_section(agent_name: str, task_name: str, agent_short_name: str, task_description: str) -> Dict:
                        try:
                            sections = result_str.split("# Agent:")
                            sections = [s.strip() for s in sections if s.strip()]
                            
                            agent_section = None
                            for section in sections:
                                if section.startswith(agent_name):
                                    agent_section = section
                                    break
                            
                            if not agent_section:
                                logger.info(f"No section found for agent {agent_name}")
                                return {
                                    "name": task_name,
                                    "description": task_description,
                                    "agent": agent_short_name,
                                    "tool_interactions": [],
                                    "final_answer": {}
                                }
                            
                            # Extract final answer
                            final_answer = {}
                            final_answer_match = re.search(r'## Final Answer:\s*({[^#]*})', agent_section, re.DOTALL | re.MULTILINE)
                            
                            if final_answer_match:
                                try:
                                    final_answer_text = final_answer_match.group(1).strip()
                                    final_answer_text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', final_answer_text, flags=re.DOTALL)
                                    final_answer = json.loads(final_answer_text)
                                except json.JSONDecodeError:
                                    logger.error(f"Failed to parse final answer JSON for {agent_name}")
                            
                            return {
                                "name": task_name,
                                "description": task_description,
                                "agent": agent_short_name,
                                "tool_interactions": [],
                                "final_answer": final_answer
                            }
                            
                        except Exception as e:
                            logger.error(f"Error in extract_agent_section for {agent_name}: {str(e)}")
                            return {
                                "name": task_name,
                                "description": task_description,
                                "agent": agent_short_name,
                                "tool_interactions": [],
                                "final_answer": {}
                            }
                    
                    response = {
                        "session_id": session_id,
                        "query": user_input,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "workflow_summary": {
                            "tasks": [
                                extract_agent_section(
                                    "Information Gathering Specialist",
                                    "Information Gathering",
                                    "Info Gatherer",
                                    "Analyze user query and chat history..."
                                ),
                                extract_agent_section(
                                    "Market Research Analyst",
                                    "Market Analysis",
                                    "Market Analyst",
                                    "Based on the investment amount..."
                                ),
                                extract_agent_section(
                                    "Investment Strategist",
                                    "Investment Strategy",
                                    "Strategist",
                                    "Create a comprehensive investment strategy..."
                                )
                            ]
                        },
                        "execution_summary": {
                            "total_agents": len(agents),
                            "total_tasks": len(tasks),
                            "execution_flow": "sequential",
                            "completion_status": "success",
                            "execution_time": datetime.datetime.now().isoformat()
                        }
                    }
                else:
                    # If no agent sections found, return the result as is
                    response = {
                        "session_id": session_id,
                        "query": user_input,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "workflow_summary": {
                            "tasks": [
                                {
                                    "name": "Investment Strategy",
                                    "description": "Create a comprehensive investment strategy...",
                                    "agent": "Strategist",
                                    "tool_interactions": [],
                                    "final_answer": result
                                }
                            ]
                        },
                        "execution_summary": {
                            "total_agents": len(agents),
                            "total_tasks": len(tasks),
                            "execution_flow": "sequential",
                            "completion_status": "success",
                            "execution_time": datetime.datetime.now().isoformat()
                        }
                    }
                
                return response
            
        except Exception as e:
            logger.error(f"Error in run_analysis: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat(),
                "query": user_input,
                "session_id": session_id
            } 