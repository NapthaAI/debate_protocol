#!/usr/bin/env python
import asyncio
from colorama import Fore, Style, init
from typing import List
from naptha_sdk.task import Task as Agent
from naptha_sdk.utils import get_logger, load_yaml
from multiagent_debate.schemas import ACLMessage, ACLPerformative, InputSchema

logger = get_logger(__name__)
# Initialize colorama
init(autoreset=True)

class DebateSimulation:
    def __init__(self, agents, max_rounds: int, initial_claim: str = "", context: str = ""):
        self.agents = agents
        self.max_rounds = max_rounds
        self.conversation = []
        self.initial_claim = initial_claim
        self.context = context
        
        # Add initial claim and context to the conversation
        if initial_claim:
            initial_message = ACLMessage(
                performative=ACLPerformative.PROPOSE,
                sender="User",
                receiver="ALL",
                content=initial_claim,
                reply_with="msg1"
            )
            self.conversation.append(initial_message)
        
        if context:
            context_message = ACLMessage(
                performative=ACLPerformative.PROPOSE,
                sender="User",
                receiver="ALL",
                content=context,
                reply_with="msg2"
            )
            self.conversation.append(context_message)

    async def run_debate(self) -> List[ACLMessage]:
        for i in range(self.max_rounds):
            logger.info(f"================== ROUND {i} ==================")
            for agent in self.agents:
                logger.info(f"================== Agent {agent.name} ==================")
                if not agent.name == "VERA_Agent":
                    message = await agent(conversation=self.conversation, agent_name=agent.name, agent_type="debate")
                    message = ACLMessage.parse_raw(message)
                    if message:
                        self.conversation.append(message)
            
            # Perform verification at the end by VeraAgent
            vera_agent = next(agent for agent in self.agents if agent.name == "VERA_Agent")
            vera_message = await vera_agent(conversation=self.conversation, agent_name=agent.name, agent_type="vera")
            vera_message = ACLMessage.parse_raw(vera_message)
            if vera_message:
                self.conversation.append(vera_message)
        
        return self.conversation

async def run(inputs, worker_node_urls=None, *args, **kwargs):
    from naptha_sdk.client.node import Node
    from naptha_sdk.schemas import AgentRunInput
    logger.info(f"Inputs: {inputs}")

    agents = [
        Agent(name="Agent_1", fn="debate_agent", worker_node_url=worker_node_urls[0], *args, **kwargs),
        Agent(name="Agent_2", fn="debate_agent", worker_node_url=worker_node_urls[0], *args, **kwargs),
        Agent(name="Agent_3", fn="debate_agent", worker_node_url=worker_node_urls[0], *args, **kwargs),
        Agent(name="Agent_4", fn="debate_agent", worker_node_url=worker_node_urls[0], *args, **kwargs),
        Agent(name="VERA_Agent", fn="debate_agent", worker_node_url=worker_node_urls[0], *args, **kwargs),
    ]    

    debate = DebateSimulation(agents, max_rounds=inputs.max_rounds, initial_claim=inputs.initial_claim, context=inputs.context)
    result = await debate.run_debate()

    print("Debate Transcript:")
    print("------------------")
    for msg in result:
        print_colored_message(msg)
    
    final_judgment = next(msg for msg in reversed(result) if msg.sender == "VERA_Agent")
    print("\nFinal Judgment:")
    print("---------------")
    print(f"{Fore.MAGENTA}{final_judgment.content}{Style.RESET_ALL}")

    return result

def print_colored_message(message: ACLMessage):
    color_map = {
        ACLPerformative.PROPOSE: Fore.GREEN,
        ACLPerformative.CHALLENGE: Fore.YELLOW,
        ACLPerformative.VERIFY: Fore.CYAN,
        ACLPerformative.CONFIRM: Fore.MAGENTA
    }
    color = color_map.get(message.performative, Fore.WHITE)
    print(f"{color}{message.sender} ({message.performative.value}): {message.content}{Style.RESET_ALL}")

if __name__ == "__main__":
    cfg_path = "multiagent_debate/component.yaml"
    cfg = load_yaml(cfg_path)

    initial_claim = "Tesla's price will exceed $250 in 2 weeks."
    context = """
Tesla's current price is $207, and recent innovations and strong Q2 results will drive the price up.

News Summary 1:
Tesla stock was lower to start a new week of trading, falling as investors worry about global growth. Shares of the electric-vehicle giant were down 7.3% in premarket trading Monday at $192.33. Stocks around the world were falling as investors fretted that weak economic data signal a recession ahead. Despite positive comments from CEO Elon Musk about Tesla’s sales, the stock has fallen about 16% this year and is struggling to overcome negative global investor sentiment.

News Summary 2:
Tesla faces growing competition and softening demand, impacting its stock price which is trading 43% below its all-time high. The company’s profitability is declining, with earnings per share shrinking 46% year-over-year in Q2 2024. Despite recent price cuts and a plan to produce a low-cost EV model, sales growth has decelerated. Tesla is also involved in autonomous self-driving software, humanoid robots, and solar energy, but these segments may take years to significantly impact revenue.
"""
    inputs = {
        "initial_claim": initial_claim,
        "context": context,
        "max_rounds": 2,
    }
    agent_run = {"consumer_id": "user:18837f9faec9a02744d308f935f1b05e8ff2fc355172e875c24366491625d932f36b34a4fa80bac58db635d5eddc87659c2b3fa700a1775eb4c43da6b0ec270d", 
                "agent_name": "multiagent_debate", "agent_run_type": "package", "worker_nodes": ["http://localhost:7001"]}
    agent_run = AgentRunInput(**flow_run)
    inputs = InputSchema(**inputs)
    orchestrator_node = Node("http://localhost:7001")

    response = asyncio.run(run(inputs, agent_run.worker_node_urls, orchestrator_node, agent_run, cfg))
    print(response)
    print("Agent Run: ", agent_run)