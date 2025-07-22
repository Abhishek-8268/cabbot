from langchain_core.messages import HumanMessage
from schemas.driver_schema import AgentState
from graph.builder import app



def run_conversation():
    """
    Manages the conversation loop with the LangGraph agent.
    """
    initial_agent_state = AgentState()
    
    print("CabSwale: Namaste! Main aapki cab booking me sahayata kar sakta hun. Aapko kis sheher se cab chaiye?")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit"]:
            print("CabSwale Sahayak: Nice to meet You ! Bye Bye.")
            break

        initial_agent_state.messages.append(HumanMessage(content=user_input))

        config = {"recursion_limit": 50}
        final_state = app.invoke({"agent_state": initial_agent_state}, config=config)
        
        ai_response = final_state['agent_state'].messages[-1]
        
        if ai_response.content:
            print(f"CabSwale : {ai_response.content}")
        
        initial_agent_state = final_state['agent_state']

if __name__ == "__main__":
    run_conversation()