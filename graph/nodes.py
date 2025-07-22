import json
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

from langchain_core.messages import ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY, DEFAULT_PAGE_LIMIT, GET_PARTNER_DATA_URL, MAX_FILTER_DEPTH
from graph.state import GraphState
from tools.driver_tools import tools
from schemas.driver_schema import AgentState
from prompts.system_prompt import get_system_prompt
from services.api_client import (
    fetch_drivers_from_api,
    make_api_request,
    construct_detailed_driver,
    get_timestamp
)

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=GOOGLE_API_KEY)
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: GraphState) -> Dict[str, Any]:
    """The primary node that decides the next action."""
    print("--- NODE: Agent ---")
    current_state: AgentState = state['agent_state']
    system_prompt = get_system_prompt(current_state)
    messages = [system_prompt] + current_state.messages
    response = llm_with_tools.invoke(messages)
    current_state.messages.append(response)
    return {"agent_state": current_state}

def tool_node(state: GraphState) -> Dict[str, Any]:
    """This node now handles the complex filtering and contact info logic."""
    print("--- NODE: Tool Executor ---")
    current_state: AgentState = state['agent_state']
    last_message = current_state.messages[-1]

    if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {}

    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args")
        tool_output = {}

        if tool_name == "filter_drivers":
            print(f"--- ACTION: Filtering drivers with criteria: {tool_args} ---")
            all_drivers = current_state.driver_profiles.values()
            
            # We only consider drivers who haven't been presented yet
            unseen_drivers = [
                d for d in all_drivers if d['existingInfo']['id'] not in current_state.presented_driver_ids
            ]
            
            # Apply the filters
            matched_drivers = []
            for driver in unseen_drivers:
                matches = True
                # Language Filter
                if 'languages' in tool_args and tool_args['languages']:
                    if not any(lang.lower() == tool_args['languages'] for lang in driver.get('languages', [])):
                        matches = False
                # Pets Filter
                if 'isPetAllowed' in tool_args and tool_args['isPetAllowed'] is not None:
                    if driver.get('isPetAllowed') != tool_args['isPetAllowed']:
                        matches = False
                # Married Filter
                if 'married' in tool_args and tool_args['married'] is not None:
                    if driver.get('married') != tool_args['married']:
                        matches = False
                
                if matches:
                    matched_drivers.append(driver)

            tool_output = {"matched_drivers": matched_drivers[:DEFAULT_PAGE_LIMIT]} # Return up to 10 matches

        elif tool_name == "get_driver_contact_info":
            driver_id = tool_args.get("driver_id_for_contact")
            driver_profile = current_state.driver_profiles.get(driver_id)
            if driver_profile:
                tool_output = {"contact_info": driver_profile.get("phoneNo")}
            else:
                tool_output = {"error": "Driver not found in cache."}
        
        else:
            # Handle simple tools like set_city and find_drivers
            selected_tool = next((t for t in tools if t.name == tool_name), None)
            if not selected_tool: raise ValueError(f"Tool '{tool_name}' not found.")
            tool_output = selected_tool.invoke(tool_args)

        tool_messages.append(ToolMessage(content=json.dumps(tool_output), tool_call_id=tool_call["id"]))

    current_state.messages.extend(tool_messages)
    return {"agent_state": current_state}

def state_updater_node(state: GraphState) -> Dict[str, Any]:
    """This node now triggers background fetching and manages state updates."""
    print("--- NODE: State Updater ---")
    current_state: AgentState = state['agent_state']
    last_message = current_state.messages[-1]
    
    if not isinstance(last_message, ToolMessage):
        return {}
    
    tool_output = json.loads(last_message.content)
    
    if "city_updated" in tool_output:
        current_state.city = tool_output["city_updated"]
        # Reset everything when the city changes
        current_state.page = 1
        current_state.driver_profiles = {}
        current_state.presented_driver_ids = []
        current_state.filters = {}
        current_state.filter_search_depth = 0
        current_state.no_more_drivers = False
        print(f"--- STATE: City updated to {current_state.city}. State reset. ---")

    if "city" in tool_output: # This comes from the find_drivers tool
        print(f"--- ACTION: Fetching page {current_state.page} of premium drivers... ---")
        new_premium_drivers = fetch_drivers_from_api(current_state.city, current_state.page, DEFAULT_PAGE_LIMIT)
        
        if new_premium_drivers:
            # --- BACKGROUND FETCHING LOGIC ---
            def fetch_and_construct_details(premium_driver):
                payload = {"partnerId": premium_driver['id'], "timestamp": get_timestamp()}
                details_response = make_api_request(GET_PARTNER_DATA_URL, payload)
                if "data" in details_response and details_response["data"]:
                    details_from_api = details_response["data"]
                    # Handle if API returns a list or a dict
                    if isinstance(details_from_api, list):
                        details_from_api = details_from_api[0]
                    
                    full_details = construct_detailed_driver(premium_driver, details_from_api)
                    if full_details:
                        return full_details['existingInfo']['id'], full_details
                return None, None

            with ThreadPoolExecutor(max_workers=10) as executor:
                results = executor.map(fetch_and_construct_details, new_premium_drivers)
                for driver_id, full_details in results:
                    if driver_id and full_details:
                        current_state.driver_profiles[driver_id] = full_details
                        print(f"--- BG FETCH: Successfully fetched details for {driver_id}")

            current_state.page += 1
        else:
            print("--- STATE: No more premium drivers found from API. ---")
            current_state.no_more_drivers = True

    if "filters_to_apply" in tool_output:
        current_state.filters.update(tool_output["filters_to_apply"])
        # When filters are applied, reset the search depth counter
        current_state.filter_search_depth = 0
        print(f"--- STATE: Filters updated to {current_state.filters}. ---")

    if "matched_drivers" in tool_output:
        matched_drivers = tool_output["matched_drivers"]
        # Add the newly presented drivers to the presented list
        for driver in matched_drivers:
            current_state.presented_driver_ids.append(driver['existingInfo']['id'])

    return {"agent_state": current_state}