from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from agents import Agent, Runner, trace , WebSearchTool
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

@dataclass
class PitchContext:
    """Context for pitch-related operations"""
    conversation_history: List[Dict[str, Any]]
    pitch_content: Optional[str] = None
    industry: Optional[str] = None
    verticals: Optional[List[str]] = None
    problem: Optional[str] = None

    def get_conversation_messages(self) -> List[Dict[str, str]]:
        """Format conversation history into messages"""
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in self.conversation_history
        ]

class PitchEvaluation(BaseModel):
    """Structured output for pitch evaluation"""
    clarity: int = Field(description="Rating from 1-5 for clarity of presentation")
    clarity_feedback: str = Field(description="Detailed feedback about clarity")
    content: int = Field(description="Rating from 1-5 for content quality")
    content_feedback: str = Field(description="Detailed feedback about content")
    structure: int = Field(description="Rating from 1-5 for pitch structure")
    structure_feedback: str = Field(description="Detailed feedback about structure")
    delivery: int = Field(description="Rating from 1-5 for delivery style")
    delivery_feedback: str = Field(description="Detailed feedback about delivery")
    feedback: str = Field(description="Overall feedback and suggestions")

class PitchContextExtraction(BaseModel):
    """Structured output for pitch context extraction"""
    industry: str = Field(description="The primary industry the pitch is focused on")
    verticals: List[str] = Field(description="Specific market segments or verticals mentioned in the pitch")
    problem: str = Field(description="The main problem or pain point the pitch addresses")
    summary: str = Field(description="Brief summary of the pitch context")

class MarketResearchResults(BaseModel):
    """Structured output for market research"""
    summary: Optional[str] = Field(
        description="Brief summary of research findings",
        default=""
    )
    competitors: Optional[List[Dict[str, Any]]] = Field(
        description="List of competitors in the problem space",
        default_factory=list
    )
    market_size: Optional[Dict[str, Any]] = Field(
        description="Market size information for the industry and verticals",
        default_factory=dict
    )
    market_size_sources: Optional[Dict[str, str]] = Field(
        description="Source URLs for each market size metric (overall, growth, projection)",
        default_factory=dict
    )
    trends: Optional[List[Dict[str, Any]]] = Field(
        description="Key market trends",
        default_factory=list
    )
    trends_source: Optional[str] = Field(
        description="Source URL for market trends information",
        default=""
    )
    growth_calculation: Optional[str] = Field(
        description="Explanation of how projected growth was calculated",
        default=""
    )

# Create agents for different purposes
context_extraction_agent = Agent[PitchContext](
    name="context_extraction_agent",
    instructions="""You are an expert at analyzing pitch transcripts and extracting key contextual information.
    Your task is to identify the following elements from the provided pitch transcript:
    
    1. Industry: Determine the primary industry the startup or product is targeting
    2. Verticals: Identify specific market segments, verticals, or niches mentioned
    3. Problem: Extract the main problem or pain point that the pitch is addressing
    
    Be specific and concise in your analysis. For each element:
    
    - Industry: Identify the broader category (e.g., "Healthcare", "Fintech", "Education")
    - Verticals: List 1-3 specific verticals mentioned (e.g., "Mental Health Apps", "B2B Payment Solutions")
    - Problem: Clearly state the main problem being solved in 1-2 sentences
    
    Also provide a brief summary (2-3 sentences) capturing the essence of the pitch context.
    
    Focus only on extracting factual information mentioned in the transcript. Do not evaluate or judge the quality of the pitch.""",
    output_type=PitchContextExtraction,
)

pitch_analysis_agent = Agent[PitchContext](
    name="pitch_analysis_agent",
    instructions="""You are an expert pitch coach. Analyze pitch presentations and provide structured feedback.
    Focus on clarity, content quality, structure, and delivery style.
    Be specific in your feedback and provide actionable suggestions for improvement.
    
    For each criterion, provide a rating and detailed feedback:
    
    - Clarity (1-5): How clear and understandable is the pitch?
      - Provide specific feedback about clarity, focusing on language choices, explanation quality, and how well ideas are communicated.
    
    - Content (1-5): How compelling and valuable is the content?
      - Provide specific feedback about content value, focusing on uniqueness, evidence/data included, value proposition, and market relevance.
    
    - Structure (1-5): How well-organized is the presentation?
      - Provide specific feedback about structure, focusing on logical flow, organization, transitions between topics, and overall narrative arc.
    
    - Delivery (1-5): How effective is the delivery style?
      - Provide specific feedback about delivery, focusing on pacing, emphasis, confidence, engagement, and overall presentation style.
    
    Also provide overall feedback summarizing key strengths and areas for improvement across all categories.
    
    Make your feedback constructive, specific, and actionable with clear examples from the pitch.""",
    output_type=PitchEvaluation,
)

chat_agent = Agent[PitchContext](
    name="chat_agent",
    instructions="""You are a helpful AI assistant specializing in startup pitches and presentations.
    Provide clear, constructive advice and engage in meaningful dialogue about pitch improvement.
    Be encouraging while maintaining honesty in your feedback.
    
    Consider:
    1. The user's specific questions or concerns
    2. The conversation history for context
    3. Previous feedback and suggestions
    4. Areas for improvement
    
    Maintain a supportive and professional tone throughout the conversation."""
)

# Create a web search agent to research market and competitors
market_research_agent = Agent(
    name="market_research_agent",
    instructions="""You are an expert market researcher specializing in competitive analysis and market sizing.
    Your task is to research and provide structured information about:
    
    1. Competitors: Find 3-5 top companies addressing the same problem space as the pitch
    2. Market Size: Research the current market size of the industry and specific verticals
    3. Market Trends: Identify 2-3 key trends in this market space
    
    Use the provided industry, verticals, and problem context to guide your research.
    Be thorough but concise in your findings, and ensure all information is up-to-date.
    
    For each competitor, provide:
    - Name: The company name
    - Description: A brief description of their offering (1-2 sentences)
    - URL: Their website URL if available
    
    For market size:
    - Overall: The overall market size (in $ billions or millions)
    - Growth: Annual growth rate (%)
    - Projection: Projected market size in 5 years if available
    
    IMPORTANT: For EACH market size metric (overall, growth, projection), you MUST provide a specific source URL where the data was found.
    
    For market trends:
    - Title: A short name for the trend
    - Description: A brief explanation of the trend and its impact
    
    Also provide:
    - A brief summary (3-4 sentences) capturing key insights from your research
    - Source URLs for market trends information
    - A brief explanation of how projected growth was calculated (e.g., compound annual growth rate formula, industry report projection, etc.)
    
    Focus on finding factual, current information from reliable sources. Be specific with numbers
    and data points where possible, citing the year of the data.
    
    Format your response as JSON with the following structure:
    {
      "summary": "Brief summary of findings",
      "competitors": [
        {"name": "Company Name", "description": "Description", "url": "URL"}
      ],
      "market_size": {
        "overall": "Size in dollars",
        "growth": "Growth rate",
        "projection": "Future projection"
      },
      "market_size_sources": {
        "overall": "URL for overall market size data",
        "growth": "URL for growth rate data",
        "projection": "URL for projected market size data"
      },
      "trends": [
        {"title": "Trend Name", "description": "Trend description"}
      ],
      "trends_source": "URL for market trends information",
      "growth_calculation": "Explanation of projected growth calculation"
    }""",
    tools=[WebSearchTool()],
)

def create_pitch_context(
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    pitch_content: Optional[str] = None
) -> PitchContext:
    """
    Create a pitch context with conversation history and pitch content.
    
    Args:
        conversation_history: Optional list of previous messages
        pitch_content: Optional pitch content to analyze
        
    Returns:
        PitchContext object with conversation history and pitch content
    """
    return PitchContext(
        conversation_history=conversation_history or [],
        pitch_content=pitch_content
    )

async def extract_pitch_context(
    pitch_content: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> PitchContextExtraction:
    """
    Extract contextual information from a pitch transcript.
    
    Args:
        pitch_content: The pitch text to analyze
        conversation_history: Optional list of previous messages
        
    Returns:
        PitchContextExtraction object containing industry, verticals, and problem
    """
    with trace("Pitch Context Extraction") as current_trace:
        # Create context with conversation history and pitch content
        context = create_pitch_context(
            conversation_history=conversation_history,
            pitch_content=pitch_content
        )
            
        # Run the extraction with context and tracing
        result = await Runner.run(
            context_extraction_agent,
            pitch_content
        )
        
        return result.final_output

async def analyze_pitch(
    pitch_content: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
    context_extraction: Optional[PitchContextExtraction] = None,
) -> PitchEvaluation:
    """
    Analyze a pitch using the pitch analysis agent.
    
    Args:
        pitch_content: The pitch text to analyze
        conversation_history: Optional list of previous messages
        context_extraction: Optional context extraction results
        
    Returns:
        PitchEvaluation object containing structured feedback
    """
    with trace("Pitch Analysis") as current_trace:
        # Create context with conversation history, pitch content, and extracted context
        context = create_pitch_context(
            conversation_history=conversation_history,
            pitch_content=pitch_content
        )
        
        # Add extracted context information if available
        if context_extraction:
            context.industry = context_extraction.industry
            context.verticals = context_extraction.verticals
            context.problem = context_extraction.problem
            
        # Run the analysis with context and tracing
        result = await Runner.run(
            pitch_analysis_agent,
            pitch_content
        )
        
        return result.final_output

async def chat_response(
    user_input: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Generate a chat response using the chat agent.
    
    Args:
        user_input: The user's message
        conversation_history: Optional list of previous messages
        
    Returns:
        String response from the agent
    """
    with trace("Chat Response") as current_trace:
        # Create context with conversation history
        context = create_pitch_context(
            conversation_history=conversation_history
        )
            
        # Generate response with context and tracing
        result = await Runner.run(
            chat_agent,
            user_input
        )
        
        return result.final_output

async def conduct_market_research(
    context_extraction: PitchContextExtraction,
) -> Dict[str, Any]:
    """
    Conduct market research based on pitch context extraction.
    
    Args:
        context_extraction: The extracted context from the pitch
        
    Returns:
        Dictionary containing structured research findings
    """
    print("="*80)
    print(f"MARKET RESEARCH STARTED FOR: {context_extraction.industry}")
    print(f"VERTICALS: {', '.join(context_extraction.verticals)}")
    print(f"PROBLEM: {context_extraction.problem}")
    print("="*80)
    
    with trace("Market Research") as current_trace:
        # Create search prompt
        search_prompt = f"""
        Research the following:
        
        Industry: {context_extraction.industry}
        Market Verticals: {', '.join(context_extraction.verticals)}
        Problem: {context_extraction.problem}
        
        Please find:
        1. Top competitors addressing this problem
        2. Current market size (in $ value)
        3. Market growth rate and projections
        4. Key market trends
        
        Provide structured, factual information with specific numbers and data points where possible.
        
        *** MANDATORY REQUIREMENT: You MUST include a specific source URL for EACH of these data points: ***
        - Overall market size figure - MUST have a source URL
        - Annual growth rate - MUST have a source URL
        - Future market projection - MUST have a source URL
        - Market trends - MUST have a source URL
        
        These source URLs are critical for our application to work correctly. Use the exact JSON format below and ensure all source fields have valid URLs.
        
        If projecting growth, explain how the projection was calculated.
        Format your response as valid JSON with this structure:
        {
          "summary": "Brief summary of findings",
          "competitors": [
            {"name": "Company Name", "description": "Description", "url": "URL"}
          ],
          "market_size": {
            "overall": "Size in dollars",
            "growth": "Growth rate",
            "projection": "Future projection"
          },
          "market_size_sources": {
            "overall": "URL for overall market size data",
            "growth": "URL for growth rate data",
            "projection": "URL for projected market size data"
          },
          "trends": [
            {"title": "Trend Name", "description": "Trend description"}
          ],
          "trends_source": "URL for market trends information",
          "growth_calculation": "Explanation of projected growth calculation"
        }
        """
        
        print("\nSENDING PROMPT TO RESEARCH AGENT:")
        print("-"*60)
        print(search_prompt.strip())
        print("-"*60)
        
        try:
            print("\nWAITING FOR AGENT RESPONSE...")
            # Run the market research with context and tracing
            result = await Runner.run(
                market_research_agent,
                search_prompt
            )
            
            # Debug the result object
            print(f"\nAGENT RESPONSE RECEIVED - Result Type: {type(result).__name__}")
            logging.info(f"Result object type: {type(result).__name__}")
            
            # Try to identify what attributes are available
            result_dir = dir(result)
            print(f"Result object attributes: {', '.join(result_dir[:10])}...")
            logging.info(f"Result object attributes: {result_dir}")
            
            # Extract JSON from response
            import re
            import json
            
            # Check for different possible attributes
            response_text = None
            for attr in ['output', 'response', 'content', 'text', 'message', 'final_output']:
                if hasattr(result, attr):
                    response_text = getattr(result, attr)
                    print(f"Using result.{attr} for response text")
                    logging.info(f"Using result.{attr}")
                    break
            
            # If no recognized attribute is found, use string representation
            if response_text is None:
                response_text = str(result)
                print("No standard attributes found, using str(result)")
                logging.info("Using str(result)")
            
            print(f"\nRAW RESPONSE PREVIEW (first 300 chars):")
            print("-"*60)
            print(f"{str(response_text)[:300]}...")
            print("-"*60)
            logging.info(f"Raw response (first 200 chars): {str(response_text)[:200]}...")
            
            # Try to find JSON in the response
            print("\nEXTRACTING JSON FROM RESPONSE...")
            json_match = re.search(r'```json\n(.*?)\n```', str(response_text), re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                print("Found JSON in code block with json marker")
                logging.info("Found JSON in code block with json marker")
            else:
                json_match = re.search(r'```\n(.*?)\n```', str(response_text), re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    print("Found JSON in generic code block")
                    logging.info("Found JSON in generic code block")
                else:
                    # Just try to use the whole response
                    json_str = str(response_text)
                    print("No code blocks found, using entire response as JSON")
                    logging.info("Using entire response as JSON")
            
            # Clean up potential issues in JSON
            json_str = json_str.strip()
            
            # Try to parse JSON
            print("\nPARSING JSON...")
            research_data = json.loads(json_str)
            print(f"Successfully parsed JSON with {len(research_data)} keys: {', '.join(research_data.keys())}")
            logging.info(f"Successfully parsed JSON with keys: {research_data.keys()}")
            
            # Validate required fields
            print("\nVALIDATING AND FILLING MISSING FIELDS...")
            if "summary" not in research_data:
                research_data["summary"] = "No summary available"
                print("- Added missing 'summary' field")
            if "competitors" not in research_data:
                research_data["competitors"] = []
                print("- Added missing 'competitors' field")
            if "market_size" not in research_data:
                research_data["market_size"] = {}
                print("- Added missing 'market_size' field")
            if "trends" not in research_data:
                research_data["trends"] = []
                print("- Added missing 'trends' field")
            
            # Ensure market_size_sources exists and has required fields
            if "market_size_sources" not in research_data:
                print("- WARNING: 'market_size_sources' not found in response, creating empty dictionary")
                logging.warning("market_size_sources not found in response, creating empty dictionary")
                research_data["market_size_sources"] = {}
            
            # Ensure search sources for all market metrics
            search_base = f"https://www.google.com/search?q="
            
            if "overall" not in research_data["market_size_sources"] or not research_data["market_size_sources"]["overall"]:
                search_query = f"{context_extraction.industry}+market+size+{research_data['market_size'].get('overall', '')}"
                research_data["market_size_sources"]["overall"] = search_base + search_query.replace(" ", "+")
                print(f"- WARNING: Added fallback source for overall market size: {research_data['market_size_sources']['overall']}")
                logging.warning(f"Missing source for overall market size, using search URL: {research_data['market_size_sources']['overall']}")
            
            if "growth" not in research_data["market_size_sources"] or not research_data["market_size_sources"]["growth"]:
                search_query = f"{context_extraction.industry}+market+growth+rate+{research_data['market_size'].get('growth', '')}"
                research_data["market_size_sources"]["growth"] = search_base + search_query.replace(" ", "+")
                print(f"- WARNING: Added fallback source for growth rate: {research_data['market_size_sources']['growth']}")
                logging.warning(f"Missing source for growth rate, using search URL: {research_data['market_size_sources']['growth']}")
            
            if "projection" not in research_data["market_size_sources"] or not research_data["market_size_sources"]["projection"]:
                search_query = f"{context_extraction.industry}+market+projection+future+{research_data['market_size'].get('projection', '')}"
                research_data["market_size_sources"]["projection"] = search_base + search_query.replace(" ", "+")
                print(f"- WARNING: Added fallback source for market projection: {research_data['market_size_sources']['projection']}")
                logging.warning(f"Missing source for market projection, using search URL: {research_data['market_size_sources']['projection']}")
            
            # Ensure trends_source exists
            if "trends_source" not in research_data or not research_data["trends_source"]:
                search_query = f"{context_extraction.industry}+market+trends+{'+'.join(context_extraction.verticals)}"
                research_data["trends_source"] = search_base + search_query.replace(" ", "+")
                print(f"- WARNING: Added fallback source for trends: {research_data['trends_source']}")
                logging.warning(f"Missing source for trends, using search URL: {research_data['trends_source']}")
            
            if "growth_calculation" not in research_data:
                research_data["growth_calculation"] = "No growth calculation provided"
                print("- Added missing 'growth_calculation' field")
                
            # Log the final data structure being returned
            print("\nFINAL RESPONSE STRUCTURE:")
            print("-"*60)
            print(f"Fields: {', '.join(research_data.keys())}")
            print(f"Market Size Sources: {research_data['market_size_sources']}")
            print(f"Trends Source: {research_data['trends_source']}")
            print(f"Competitors: {len(research_data['competitors'])}")
            print(f"Trends: {len(research_data['trends'])}")
            print("="*80)
            
            logging.info(f"Returning research data with fields: {research_data.keys()}")
            logging.info(f"market_size_sources: {research_data['market_size_sources']}")
            logging.info(f"trends_source: {research_data['trends_source']}")
                
            return research_data
        except Exception as e:
            # Log the details of the error
            print("\nERROR IN MARKET RESEARCH AGENT:")
            print("-"*60)
            print(f"Error: {str(e)}")
            print("See logs for full stack trace")
            print("-"*60)
            
            logging.error(f"Error in market research agent: {str(e)}")
            logging.exception("Full exception details:")
            
            # Generate default search URLs
            search_base = f"https://www.google.com/search?q="
            overall_search = search_base + f"{context_extraction.industry}+market+size".replace(" ", "+")
            growth_search = search_base + f"{context_extraction.industry}+market+growth+rate".replace(" ", "+")
            projection_search = search_base + f"{context_extraction.industry}+market+projection+2030".replace(" ", "+")
            trends_search = search_base + f"{context_extraction.industry}+market+trends+{'+'.join(context_extraction.verticals)}".replace(" ", "+")
            
            print("\nGENERATING FALLBACK RESPONSE WITH SEARCH URLS:")
            print(f"- Overall Market Size: {overall_search}")
            print(f"- Growth Rate: {growth_search}")
            print(f"- Projection: {projection_search}")
            print(f"- Trends: {trends_search}")
            print("="*80)
            
            # Provide a fallback response with search URLs
            return {
                "summary": "Unable to complete market research due to an error.",
                "competitors": [],
                "market_size": {"overall": "Unknown"},
                "trends": [],
                "market_size_sources": {
                    "overall": overall_search,
                    "growth": growth_search,
                    "projection": projection_search
                },
                "trends_source": trends_search,
                "growth_calculation": ""
            } 