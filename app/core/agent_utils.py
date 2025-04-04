from agents import Agent, Runner, trace , WebSearchTool
from app.schemas.schemas import PitchContext, PitchContextExtraction, PitchEvaluation, PitchDeckContent, JSXPitchDeckOutput, PitchDeckResponse
from typing import Optional, List, Dict, Any

import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()


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
    
    *** CRITICAL REQUIREMENT: For EACH market size metric (overall, growth, projection), you MUST provide a specific source URL where the data was found. This is a mandatory requirement. If you can't find a source URL, provide the most relevant search result URL. ***
    
    For market trends:
    - Title: A short name for the trend
    - Description: A brief explanation of the trend and its impact
    
    Also provide:
    - A brief summary (3-4 sentences) capturing key insights from your research
    - Source URLs for market trends information (MANDATORY)
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
    }
    
    SOURCES ARE MANDATORY - You must include source URLs for all market data.
    """,
    tools=[WebSearchTool()],
)

# Create the pitch deck content generation agent
pitch_deck_content_agent = Agent[PitchContext](
    name="pitch_deck_content_agent",
    instructions="""You are an expert pitch deck consultant specializing in creating compelling, concise content for startup pitches.
    
    Your task is to generate high-quality content for each slide in a pitch deck based on the provided context from previous analyses.
    You will receive information about the industry, market verticals, problem being solved, and market research.
    
    First, conduct ONE ROUND of web search to gather the most current and relevant information about:
    1. Current industry dynamics and challenges
    2. Why this is the right time to address the problem (market timing)
    3. Successful pitch deck examples in this industry
    
    Then, use this research along with the provided context to create professional, compelling content for each slide:
    
    1. OVERVIEW SLIDE:
       - Create a concise business summary
       - Highlight key value proposition
       - Describe target market/customers
    
    2. PROBLEM SLIDE:
       - Clearly articulate customer pain points
       - Explain limitations of current solutions
       - Identify specific market gap
    
    3. WHY NOW SLIDE:
       - Explain market timing
       - Identify relevant trends or shifts
       - Describe why this moment is opportune
    
    4. SOLUTION SLIDE:
       - Create a compelling headline for your solution
       - Develop 3 key features with clear, benefit-focused descriptions
       - Each feature should address an aspect of the problem
    
    5. MARKET OPPORTUNITY SLIDE:
       - Provide realistic market size values (TAM, SAM, Target Market, Market Share)
       - Write concise descriptions for each market segment
       - Use the market research data provided or found in your search
    
    Write in a professional, compelling style with:
    - Concise, impactful language (aim for 15-25 words per description)
    - Clear value propositions
    - Evidence-based claims where possible
    - Concrete rather than abstract language
    """,
    tools=[WebSearchTool()],
    output_type=PitchDeckContent,
)

# Create a new agent for JSX pitch deck generation
jsx_pitch_deck_agent = Agent(
    name="jsx_pitch_deck_agent",
    instructions="""You are an expert React developer specializing in creating stunning, professional pitch deck pages using JSX.
    
    Your task is to generate a beautiful, visually impressive React component in JSX format that presents a startup pitch deck
    based on the provided content. The JSX should be valid, well-formatted, and use Tailwind CSS for styling.
    
    Adhere to these professional design principles:
    
    1. Use a professional color scheme with a primary brand color and complementary accent colors
    2. Apply consistent spacing and visual hierarchy with clear section differentiation
    3. Incorporate visually engaging elements like gradient backgrounds, subtle shadows, and well-styled cards
    4. Use modern, clean typography with proper font sizing and weight hierarchy
    5. Add professional micro-interactions (hover effects, transitions) that enhance usability
    6. Ensure excellent responsive design that looks great on all screen sizes
    7. Include visualization elements such as simulated charts or graphs where appropriate
    8. Use data visualization techniques for market sizing and growth metrics
    9. Add iconography where it enhances understanding (using React Icons)
    10. Create visual distinctions between different types of content (problem vs. solution)
    
    Technical requirements:
    
    1. Return ONLY JSX code, with no explanations, markdown formatting, or comments
    2. Create a single functional React component that contains the entire pitch deck
    3. Use Tailwind CSS for styling and responsive design
    4. Include necessary imports at the top, especially for React Icons:
       ```
       import { FaChartPie, FaLightbulb, FaRocket, FaUsers, FaChartLine } from 'react-icons/fa';
       import { BiTrendingUp, BiTargetLock, BiTime } from 'react-icons/bi';
       ```
    5. Use semantic HTML elements and appropriate heading hierarchy
    6. Ensure the component is fully responsive with mobile-first design
    7. Use `className` instead of `class` for CSS classes
    8. Structure the code cleanly with logical section organization
    9. Create simulated chart components using divs, borders and background colors (don't rely on external chart libraries)
    10. Add subtle animations and transitions with Tailwind's hover, focus, and group classes
    
    The output should be a complete React component that can be directly inserted into a Next.js application.
    
    Structure the pitch deck with these visually distinct sections:
    1. Hero header with company name, tagline, and visual appeal
    2. Overview section with visual highlights of key points
    3. Problem section with visual representation of the pain points
    4. Why Now section with timeline or trend visualization
    5. Solution section with visual feature highlights
    6. Market section with market size visualization (chart/graph representation)
    
    Example of quality design elements to include:
    - Gradient backgrounds
    - Card-based designs with shadows
    - Icon integration
    - Visual data representations
    - Color-coded sections
    - Consistent spacing
    - Responsive grid layouts
    - Interactive elements (hover states, etc.)
    
    Your final output should look something like:

    ```jsx
    import { FC } from 'react';
    import { FaChartPie, FaLightbulb, FaRocket, FaUsers } from 'react-icons/fa';
    
    const PitchDeck: FC = () => {
      return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            {/* Hero Section with visual impact */}
            <header className="text-center mb-16 py-12 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-2xl shadow-xl text-white">
              <h1 className="text-5xl font-bold mb-3">Company Name</h1>
              <p className="text-xl font-light max-w-2xl mx-auto">Compelling tagline that captures essence</p>
            </header>
            
            {/* Visually distinct sections with quality design elements */}
          </div>
        </div>
      );
    };
    
    export default PitchDeck;
    ```
    
    Only return the JSX code, nothing else. Make sure all necessary React icon imports are included.""",
    output_type=JSXPitchDeckOutput,
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
        
        These source URLs are critical for our application to work correctly. Use the exact JSON format in the instructions.
        
        If projecting growth, explain how the projection was calculated.
        Format your response as valid JSON matching the structure in the instructions.
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
                    try:
                        response_text = getattr(result, attr)
                        print(f"Using result.{attr} for response text (type: {type(response_text)})")
                        logging.info(f"Using result.{attr} (type: {type(response_text)})")
                        break
                    except Exception as attr_error:
                        print(f"Error accessing attribute {attr}: {str(attr_error)}")
                        logging.error(f"Error accessing attribute {attr}: {str(attr_error)}")
            
            # If no recognized attribute is found, use string representation
            if response_text is None:
                try:
                    response_text = str(result)
                    print("No standard attributes found, using str(result)")
                    logging.info("Using str(result)")
                except Exception as str_error:
                    print(f"Error converting result to string: {str_error}")
                    logging.error(f"Error converting result to string: {str_error}")
                    response_text = "Error: Could not extract response text"
            
            print(f"\nRAW RESPONSE PREVIEW (first 300 chars):")
            print("-"*60)
            print(f"{str(response_text)[:300]}...")
            print("-"*60)
            logging.info(f"Raw response (first 200 chars): {str(response_text)[:200]}...")
            
            # Try to find JSON in the response
            print("\nEXTRACTING JSON FROM RESPONSE...")
            try:
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
                print(f"JSON string to parse (first 200 chars): {json_str[:200]}...")
                research_data = json.loads(json_str)
                print(f"Successfully parsed JSON with {len(research_data)} keys: {', '.join(research_data.keys())}")
                logging.info(f"Successfully parsed JSON with keys: {research_data.keys()}")
            except Exception as json_error:
                print(f"ERROR PARSING JSON: {str(json_error)}")
                logging.error(f"Error parsing JSON: {str(json_error)}")
                
                # Try direct access if JSON parsing fails
                try:
                    if hasattr(result, 'final_output') and isinstance(result.final_output, dict):
                        research_data = result.final_output
                        print(f"Using result.final_output directly as dictionary")
                        logging.info(f"Using result.final_output directly as dictionary")
                    else:
                        raise ValueError("Could not extract JSON from response")
                except Exception as direct_error:
                    print(f"ERROR USING DIRECT OUTPUT: {str(direct_error)}")
                    logging.error(f"Error using direct output: {str(direct_error)}")
                    raise json_error  # Re-raise the original JSON error
            
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

async def generate_pitch_deck_content(
    context_extraction: PitchContextExtraction,
    market_research: Dict[str, Any] = None,
    pitch_evaluation: PitchEvaluation = None,
) -> PitchDeckResponse:
    """
    Generate pitch deck content based on context extraction and optional market research.
    
    Args:
        context_extraction: The extracted context from the pitch
        market_research: Optional market research results
        pitch_evaluation: Optional pitch evaluation results
        
    Returns:
        PitchDeckResponse object containing pitch deck content and JSX code
    """
    print("="*80)
    print(f"PITCH DECK CONTENT GENERATION STARTED FOR: {context_extraction.industry}")
    print(f"VERTICALS: {', '.join(context_extraction.verticals)}")
    print(f"PROBLEM: {context_extraction.problem}")
    print("="*80)
    
    # Create the prompt with all available context
    prompt = f"""
    Generate content for a pitch deck with the following context:
    
    INDUSTRY: {context_extraction.industry}
    VERTICALS: {', '.join(context_extraction.verticals)}
    PROBLEM: {context_extraction.problem}
    SUMMARY: {context_extraction.summary}
    
    """
    
    # Add market research context if available
    if market_research:
        prompt += f"""
        MARKET RESEARCH:
        
        Market Size: {market_research.get('market_size', {}).get('overall', 'Not available')}
        Growth Rate: {market_research.get('market_size', {}).get('growth', 'Not available')}
        Future Projection: {market_research.get('market_size', {}).get('projection', 'Not available')}
        
        Competitors: {', '.join([comp.get('name', '') for comp in market_research.get('competitors', [])])}
        
        Market Trends:
        {' '.join([f"- {trend.get('title', '')}" for trend in market_research.get('trends', [])])}
        """
    
    # Add pitch evaluation feedback if available
    if pitch_evaluation:
        prompt += f"""
        PITCH FEEDBACK:
        
        Content Feedback: {pitch_evaluation.content_feedback}
        Structure Feedback: {pitch_evaluation.structure_feedback}
        """
    
    prompt += """
    Based on this context and your web search, create compelling content for each slide in the pitch deck.
    Follow the JSON structure exactly as specified for the PitchDeckContent output type.
    """
    
    print("\nSENDING PROMPT TO PITCH DECK CONTENT AGENT:")
    print("-"*60)
    print(prompt.strip())
    print("-"*60)
    
    try:
        print("\nWAITING FOR AGENT RESPONSE...")
        # Run the pitch deck content generation with tracing
        with trace("Pitch Deck Content Generation") as current_trace:
            result = await Runner.run(
                pitch_deck_content_agent,
                prompt
            )
        
        print("\nAGENT RESPONSE RECEIVED")
        
        # Convert the Pydantic model to a PitchDeckResponse object
        deck_content = result.final_output
        if isinstance(deck_content, PitchDeckContent):
            print("Converting Pydantic model to PitchDeckResponse")
            deck_content_dict = deck_content.dict()
        else:
            print(f"Response is type {type(deck_content)}, attempting to convert to dict")
            # Create a simple dictionary representation
            deck_content_dict = {
                "overview": str(getattr(deck_content, "overview", "No overview content")),
                "problem": str(getattr(deck_content, "problem", "No problem content")),
                "whynow": str(getattr(deck_content, "whynow", "No why now content")),
                "solution": str(getattr(deck_content, "solution", "No solution content")),
                "market": str(getattr(deck_content, "market", "No market content"))
            }
        
        # Now generate the JSX code based on the content
        jsx_prompt = f"""
        Create a beautiful, professional pitch deck page using JSX and Tailwind CSS for the following startup:
        
        Industry: {context_extraction.industry}
        Problem: {context_extraction.problem}
        
        SLIDE CONTENT:
        
        OVERVIEW:
        {deck_content_dict["overview"]}
        
        PROBLEM:
        {deck_content_dict["problem"]}
        
        WHY NOW:
        {deck_content_dict["whynow"]}
        
        SOLUTION:
        {deck_content_dict["solution"]}
        
        MARKET:
        {deck_content_dict["market"]}
        
        MARKET RESEARCH:
        {market_research["summary"] if market_research and "summary" in market_research else ""}
        
        Competitors: {", ".join([comp.get("name", "Unknown") for comp in market_research.get("competitors", [])][:3]) if market_research else ""}
        
        Market Size: {market_research.get("market_size", {}).get("overall", "Unknown") if market_research else "Unknown"}
        Market Growth: {market_research.get("market_size", {}).get("growth", "Unknown") if market_research else "Unknown"}
        
        DESIGN REQUIREMENTS:
        
        1. Use a modern, professional design with a cohesive color palette derived from the industry
        2. For {context_extraction.industry}, consider using these color schemes:
           - Technology/SaaS: Blue, purple gradients with white/light backgrounds
           - Healthcare: Soft blues and greens with clean white space
           - Finance: Navy blue, teal, with subtle gold accents
           - Education: Sky blue, orange accents, warm colors
           - E-commerce: Vibrant colors with clean white space
        
        3. Create visualizations for data points:
           - Use a simulated pie chart or bar chart for market size data
           - Create a timeline visualization for the Why Now section
           - Add feature cards with icons for the Solution section
        
        4. Use iconography appropriate to {context_extraction.industry} industry
        5. Include subtle animations and transitions (hover effects, etc.)
        6. Ensure the design is fully responsive and looks great on all devices
        7. Use visual hierarchy to draw attention to key points
        8. Incorporate white space effectively for a clean, professional look
        
        The final JSX code must be complete and ready to use within a Next.js application, with all necessary imports.
        """
        
        print("\nGENERATING JSX COMPONENT...")
        with trace("JSX Pitch Deck Generation") as jsx_trace:
            jsx_result = await Runner.run(
                jsx_pitch_deck_agent,
                jsx_prompt
            )
        
        # Add the JSX code to the response
        jsx_code = jsx_result.final_output.jsx_code
        
        # Strip out any markdown code block markers if they exist
        if jsx_code.startswith("```") and jsx_code.endswith("```"):
            jsx_code_lines = jsx_code.split("\n")
            if jsx_code_lines[0].startswith("```"):
                jsx_code_lines = jsx_code_lines[1:]
            if jsx_code_lines[-1].startswith("```"):
                jsx_code_lines = jsx_code_lines[:-1]
            jsx_code = "\n".join(jsx_code_lines)
        
        # Return a PitchDeckResponse object
        return PitchDeckResponse(
            overview=deck_content_dict["overview"],
            problem=deck_content_dict["problem"],
            whynow=deck_content_dict["whynow"],
            solution=deck_content_dict["solution"],
            market=deck_content_dict["market"],
            jsx_code=jsx_code
        )
        
    except Exception as e:
        print(f"\nERROR IN PITCH DECK CONTENT AGENT: {str(e)}")
        logging.error(f"Error generating pitch deck content: {str(e)}")
        
        # Return default structure if error occurs
        default_content = PitchDeckContent(
            overview="Default overview content due to error",
            problem="Default problem content due to error",
            whynow="Default why now content due to error",
            solution="Default solution content due to error",
            market="Default market content due to error"
        )
        
        return PitchDeckResponse(
            overview=default_content.overview,
            problem=default_content.problem,
            whynow=default_content.whynow,
            solution=default_content.solution,
            market=default_content.market,
            jsx_code="// Error generating JSX component"
        ) 