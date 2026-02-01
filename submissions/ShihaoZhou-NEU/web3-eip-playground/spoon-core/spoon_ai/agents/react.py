from spoon_ai.agents.base import BaseAgent
from spoon_ai.schema import AgentState
from abc import abstractmethod

class ReActAgent(BaseAgent):
    
    @abstractmethod
    async def think(self) -> bool:
        raise NotImplementedError("Subclasses must implement this method")
    
    @abstractmethod
    async def act(self) -> str:
        raise NotImplementedError("Subclasses must implement this method")
    
    async def step(self) -> str:
        should_act = await self.think()
        if not should_act:
            self.state = AgentState.FINISHED
            return "Thinking completed. No action needed. Task finished."
        
        return await self.act()