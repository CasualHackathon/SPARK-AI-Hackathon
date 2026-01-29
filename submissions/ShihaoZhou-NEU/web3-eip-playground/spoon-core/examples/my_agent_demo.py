from spoon_ai.agents.toolcall import ToolCallAgent
from spoon_ai.tools import ToolManager
from spoon_ai.tools.base import BaseTool
from spoon_ai.chat import ChatBot
from pydantic import Field
from dotenv import load_dotenv
import aiohttp
import asyncio

load_dotenv(override=True)
# ---------------------------- 1. Smart Weather Tool ----------------------------
class SmartWeatherTool(BaseTool):
    """Smart Weather Tool"""
    name: str = "smart_weather"
    description: str = "Get weather and outfit suggestions for a city."
    parameters: dict = {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g., 'Beijing'"
            }
        },
        "required": ["city"]
    }

    async def execute(self, city: str) -> str:
        # Step 1: Get latitude & longitude
        geocode_url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"

        async with aiohttp.ClientSession() as session:
            async with session.get(geocode_url) as resp:
                if resp.status != 200:
                    return f"Failed to obtain the geographic location, status code:{resp.status}"
                geocode_data = await resp.json()

        if not geocode_data:
            return f"Unable to find geographic information for city {city}"

        lat = geocode_data[0]["lat"]
        lon = geocode_data[0]["lon"]

        # Step 2: Get weather info
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        )

        async with aiohttp.ClientSession() as session:
            async with session.get(weather_url) as resp:
                if resp.status != 200:
                    return f"Failed to obtain weather data, status code:{resp.status}"
                weather_data = await resp.json()

        current_weather = weather_data.get("current_weather", {})
        temperature = current_weather.get("temperature")

        # Clothing Tips
        if temperature is None:
            outfit = "Unable to obtain temperature, unable to provide clothing suggestions"
        elif temperature < 5:
            outfit = "It is recommended to wear a down jacket or thick coat"
        elif 5 <= temperature < 15:
            outfit = "A coat or jacket is recommended."
        elif 15 <= temperature < 25:
            outfit = "Long sleeves or a light jacket are recommended."
        else:
            outfit = "The weather is hot, so it is recommended to wear short sleeves or cool clothes"

        return (
        f"📍 City: {city}\n"
        f"🌡 Current temperature: {temperature}°C\n"
        f"👕 Clothing suggestion: {outfit}\n"
        )


# ---------------------------- 2. Agent Definition ----------------------------
class MyInfoAgent(ToolCallAgent):
    """
    An intelligent assistant capable of performing useful information queries.
    Supports tools to retrieve GitHub statistics,
    and provide localized weather with outfit suggestions.
    """

    name: str = "my_info_agent"
    description: str = (
        "A smart assistant that can:\n"
        "1. Provide current weather and outfit suggestions for a given city.\n"
    )

    system_prompt: str = """
    You are a helpful assistant with access to tools. You can:

    1. Get current weather conditions and clothing suggestions for a specified city.

    For each user question, decide whether to invoke a tool or answer directly.
    If a tool's result isn't sufficient, analyze the result and guide the next steps clearly.
    """

    next_step_prompt: str = (
        "Based on the previous result, decide what to do next. "
        "If the result is incomplete, consider using another tool or asking for clarification."
    )

    max_steps: int = 5

    available_tools: ToolManager = Field(default_factory=lambda: ToolManager([
        SmartWeatherTool(),
    ]))


async def main():
    print("=== Using InfoAssistantAgent with New LLM Architecture ===")

    # Use LLM manager architecture (only option now)
    info_agent = MyInfoAgent(
        llm=ChatBot(
            llm_provider="openai",
            model_name="gpt-4.1"
        )
    )
    print("✓ Using LLM manager architecture")

    # Reset the Agent state
    info_agent.clear()

    # Run the Agent
    print("\n🤖 Agent is processing your request...")
    response = await info_agent.run("What is the weather like in hongkong today?")
    print(f"\n📋 Answer: {response}\n")

    # Show agent statistics if using new architecture
    if hasattr(info_agent.llm, 'use_llm_manager') and info_agent.llm.use_llm_manager:
        try:
            from spoon_ai.llm.manager import get_llm_manager
            manager = get_llm_manager()
            stats = manager.get_stats()
            print("📊 LLM Manager Statistics:")
            print(f"  - Default provider: {stats['manager']['default_provider']}")
            print(f"  - Fallback chain: {stats['manager']['fallback_chain']}")
            print(f"  - Load balancing: {stats['manager']['load_balancing_enabled']}")
        except Exception as e:
            print(f"⚠ Could not retrieve statistics: {e}")

if __name__ == "__main__":
    asyncio.run(main())
