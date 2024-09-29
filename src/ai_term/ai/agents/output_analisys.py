from typing import TypedDict
from langgraph.graph import START, END, StateGraph

from ai_term.ai.llm_wrapper import LLMWrapper
from ai_term.ai.agents.persist_predictions import CommandPredictions
from ai_term.config import Config, Colors
from ai_term.symbols import replace_symbols

verbose = False

class AgentState(TypedDict):
    terminal_history: list[dict[str, str]]
    predictions: CommandPredictions

class OutputAnalysisAgent():

    def __init__(self, verbose=False):
        self.llm = LLMWrapper("output_review", verbose=verbose)
        self.stream_callback = None
        self.command_stream_callback = None
        self.graph = None
        self.runnable = None

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_command_stream_callback(self, callback):
        self.command_stream_callback = callback

    def analyze(self, state):
        if (verbose): Colors.print("system", "> analyzing stdout and stderr")
        history = state["terminal_history"]
        if (Config.USE_INSTRUCTOR):
            predictions = self.analyze_instr(history)
        else:
            predictions = self.analyze_raw(history)
        
        for cmd in predictions.commands:
            if self.command_stream_callback:
                self.command_stream_callback(cmd)

        if (verbose): Colors.print("ai_output", "review: ", predictions)
        return {
            "predictions": predictions,
        }

    def analyze_raw(self, history):
        raw_output = ""
        history = replace_symbols(str(history))
        for line in self.llm.stream({"terminal_history": history}):
            if self.stream_callback:
                self.stream_callback(line)
            raw_output += line
        predictions = CommandPredictions.parse(raw_output)
        return predictions

    def analyze_instr(self, history):
        predictions = self.llm.run_structured(CommandPredictions, {"terminal_history": history})
    
    def create_runnable(self):
        graph = StateGraph(AgentState)
        
        graph.add_node("output_reviewer", self.analyze)
        graph.add_node("print_output_analysis", CommandPredictions.print_predictions)
        graph.add_node("persist_predictions", CommandPredictions.persist_predictions)
        
        graph.add_edge(START, "output_reviewer")
        graph.add_edge("output_reviewer", "print_output_analysis")
        graph.add_edge("print_output_analysis", "persist_predictions")
        graph.add_edge("persist_predictions", END)
        
        self.graph = graph
        self.runnable = graph.compile()

    def run(self, history):
        if self.runnable is None:
            self.create_runnable()
        return self.runnable.invoke({"terminal_history" : history})

    def get_state(self):
        return self.runnable.get_state()
