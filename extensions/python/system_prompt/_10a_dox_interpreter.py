from helpers.extension import Extension
from agent import LoopData


class DoxInterpreter(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        prompt = self.agent.read_prompt("agent.system.dox_interpreter.md")
        if prompt:
            system_prompt.append(prompt)
