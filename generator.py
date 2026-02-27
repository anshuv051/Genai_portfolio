import os
from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import json
import re

load_dotenv()

def safe_json_parse(response_content: str) -> Dict:
    """Safely parse JSON from LLM response, handling common issues."""
    # First, try to extract JSON from markdown code blocks
    content = response_content.strip()
    
    # Remove markdown code block markers
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    
    content = content.strip()
    
    # Try standard JSON parsing first
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    
    # Try to fix common JSON issues
    # 1. Fix unterminated strings by finding the last valid JSON object
    try:
        # Find the first { and last }
        first_brace = content.find('{')
        last_brace = content.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = content[first_brace:last_brace + 1]
            return json.loads(json_str)
    except:
        pass
    
    # 2. Try to fix escaped characters and common issues
    try:
        # Replace common issues
        fixed = content.replace("'", '"').replace('\n', ' ').replace('  ', ' ')
        # Remove any trailing commas before closing braces/brackets
        fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
        return json.loads(fixed)
    except:
        pass
    
    # If all else fails, raise an error
    raise ValueError(f"Could not parse JSON from response: {content[:100]}...")

class GraphState(TypedDict):
    resume_text: str
    structured_data: Dict
    portfolio_content: Dict
    error: str
    api_key: Optional[str]

def get_llm(api_key: str = None):
    return ChatOpenAI(
        model="openai/gpt-3.5-turbo",
        openai_api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
    )

def extract_resume_node(state: GraphState, api_key: str = None):
    """Parses resume text into structured JSON."""
    llm = get_llm(api_key)
    prompt = f"""
    Extract the following information from this resume and return it as a valid JSON object:
    - full_name
    - contact_info (email, phone, linkedin)
    - profile_image: Extract ANY image URL found in the resume, such as:
      * LinkedIn profile URLs (e.g., linkedin.com/in/username)
      * Personal website/portfolio URLs that might have photos
      * Any direct image URLs (ending in .jpg, .jpeg, .png, .webp)
      * If NO image URL is found, set to null
    - summary (a professional 2-3 sentence bio)
    - skills (list of strings)
    - experience (list of objects with keys: job_role, company, dates, description)
    - projects (list of objects with keys: name, tech_stack, description, github_url, demo_url)
    - education (list of objects: degree, school, dates)

    IMPORTANT: 
    1. Search the entire resume for any URLs. 
    2. Return ONLY valid JSON - no markdown code blocks, no explanations.
    3. Ensure all strings are properly escaped.
    4. Use double quotes for all strings.
    
    Resume Text:
    {state['resume_text']}
    """
    
    response = llm.invoke([
        SystemMessage(content="You are an expert resume parser. Respond ONLY with valid raw JSON. No markdown, no explanations."),
        HumanMessage(content=prompt)
    ])
    
    try:
        data = safe_json_parse(response.content)
        return {"structured_data": data}
    except Exception as e:
        return {"error": f"Failed to parse JSON: {str(e)}"}

def write_portfolio_node(state: GraphState, api_key: str = None):
    """Expands structured data into creative web content."""
    llm = get_llm(api_key)
    data = state['structured_data']
    
    # Extract contact info from structured_data
    contact_info = data.get('contact_info', {})
    
    prompt = f"""
    Based on this professional data, generate high-quality web content for a multi-page portfolio:
    
    Data: {json.dumps(data)}
    
    Generate content for 4 sections:
    1. Home Page: A catchy hero title and a compelling personal introduction.
    2. Skills Page: Group the skills into categories (e.g. Core Tech, Tools, Soft Skills).
       CRITICAL: 'skills' MUST be a DICTIONARY where keys are category names and values are LISTS of strings.
    3. Experience Page: Rewrite the experience descriptions to be more impact-oriented. 
       CRITICAL: 'experience' MUST be a LIST of objects. Each object MUST have: 'job_role', 'company', 'dates', 'description'.
    4. Projects Page: Enriched descriptions for each project.
       CRITICAL: 'projects' MUST be a LIST of objects. Each object MUST have: 'name', 'tech_stack', 'description', 'github_url', 'demo_url'.
    
    Return as a JSON object with keys: 'home', 'skills', 'experience', 'projects', 'contact'.
    
    IMPORTANT: 
    1. For the 'contact' key, include: email, linkedin, github, phone.
    2. Return ONLY valid raw JSON - no markdown code blocks, no explanations.
    3. Use double quotes for all strings.
    """
    
    response = llm.invoke([
        SystemMessage(content="You are a professional website copywriter. Respond ONLY with valid raw JSON. No markdown, no explanations."),
        HumanMessage(content=prompt)
    ])
    
    try:
        content = safe_json_parse(response.content)
        return {"portfolio_content": content}
    except Exception as e:
        return {"error": f"Failed to generate content: {str(e)}"}

# Build Workflow
workflow = StateGraph(GraphState)

def extract_wrapper(state):
    return extract_resume_node(state, state.get("api_key"))

def write_wrapper(state):
    return write_portfolio_node(state, state.get("api_key"))

workflow.add_node("extract", extract_wrapper)
workflow.add_node("write", write_wrapper)

workflow.set_entry_point("extract")
workflow.add_edge("extract", "write")
workflow.add_edge("write", END)

app_graph = workflow.compile()

def generate_portfolio(resume_text: str, api_key: str = None):
    initial_state = {
        "resume_text": resume_text, 
        "structured_data": {}, 
        "portfolio_content": {}, 
        "error": "",
        "api_key": api_key
    }
    final_state = app_graph.invoke(initial_state)
    return {
        "structured_data": final_state.get("structured_data"),
        "portfolio_content": final_state.get("portfolio_content"),
        "error": final_state.get("error")
    }

