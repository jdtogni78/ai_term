from typing import TypedDict
from langgraph.graph import START, END, StateGraph

from ai_term.ai.llm_wrapper import LLMWrapper
from ai_term.ai.agents.persist_predictions import CommandPredictions
from ai_term.symbols import replace_symbols
from ai_term.config import Config

verbose = False

class AgentState(TypedDict):
    request: str
    predictions: CommandPredictions

class SuggestionAgent:

    def __init__(self):
        self.llm = LLMWrapper("suggestion")
        self.stream_callback = None
        self.command_stream_callback = None
        self.graph = None
        self.runnable = None

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_command_stream_callback(self, callback):
        self.command_stream_callback = callback

    def make_suggestion(self, state):
        # remove the ai_cmd from the command
        request = state["request"]  
        if (verbose): print(self.color + "> requesting ai help: ", request)
        # Generate suggestions based on context
        if Config.USE_INSTRUCTOR:
            predictions = self.make_suggestions_instr(state["request"])
        else:
            predictions = self.make_suggestions_raw(state["request"])
        
        for cmd in predictions.commands:
            if self.command_stream_callback:
                self.command_stream_callback(cmd.command)

        return {
            "predictions": predictions,
        }

    def make_suggestions_raw(self, request):
        raw_output = ""
        request = replace_symbols(str(request))
        if (verbose): print(request)
        for line in self.llm.stream({"request": request}):
            if self.stream_callback:
                self.stream_callback(line)
            raw_output += line
        predictions = CommandPredictions.parse(raw_output)
        return predictions

    def make_suggestions_instr(self, request):
        return self.llm.run_structured(CommandPredictions, {"request": request})
    
    def create_runnable(self):
        graph = StateGraph(AgentState)
        graph.add_node("suggestion_agent", self.make_suggestion)
        graph.add_node("print_suggestion", CommandPredictions.print_predictions)
        graph.add_node("persist_predictions", CommandPredictions.persist_predictions)
        
        graph.add_edge(START, "suggestion_agent")
        graph.add_edge("suggestion_agent", "print_suggestion")
        graph.add_edge("print_suggestion", "persist_predictions")
        graph.add_edge("persist_predictions", END)
        
        self.graph = graph
        self.runnable = graph.compile()

    def run(self, request): #output is Suggestion
        if self.runnable is None:
            self.create_runnable()
        return self.runnable.invoke({"request" : request})

    def get_state(self):
        return self.runnable.get_state()
