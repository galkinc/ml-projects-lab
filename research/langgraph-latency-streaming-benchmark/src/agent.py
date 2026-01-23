from typing import TypedDict, List
from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from config import settings

class AgentState(TypedDict):
    messages: List[BaseMessage]

# Initialize Bedrock Chat Model
creds = settings.get_aws_credentials()
model = ChatBedrock(
    model_id=settings.bedrock.model_id,
    region_name=creds.get("region_name"),
    aws_access_key_id=creds.get("aws_access_key_id"),
    aws_secret_access_key=creds.get("aws_secret_access_key"),
    model_kwargs={"temperature": settings.bedrock.temperature},
    streaming=True
)

def call_model(state: AgentState):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}

# Build Graph
builder = StateGraph(AgentState)
builder.add_node("agent", call_model)
builder.add_edge(START, "agent")
builder.add_edge("agent", END)

# Persistence
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
