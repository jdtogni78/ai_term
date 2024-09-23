from typing import TypedDict
from langgraph.graph import START, END, StateGraph
import colorama

from ai_term.ai.llm_wrapper import LLMWrapper
from ai_term.ai.agents.persist_predictions import CommandPredictions

verbose = False

class AgentState(TypedDict):
    terminal_history: list[dict[str, str]]
    predictions: CommandPredictions

class OutputAnalysisAgent():

    def __init__(self):
        self.llm = LLMWrapper("prompts/prompt_output_review.md")
        self.color = colorama.Fore.GREEN
        self.ai_color = colorama.Fore.YELLOW
        self.stream_callback = None
        self.command_stream_callback = None
        self.graph = None
        self.runnable = None

    def set_stream_callback(self, callback):
        self.stream_callback = callback

    def set_command_stream_callback(self, callback):
        self.command_stream_callback = callback

    def analyze(self, state):
        if (verbose): print(self.color + "> analyzing stdout and stderr")
        history = state["terminal_history"]
        predictions = self.llm.run_structured(CommandPredictions, {"terminal_history": history})
        
        for cmd in predictions.commands:
            if self.command_stream_callback:
                self.command_stream_callback(cmd)

        if (verbose): print(self.ai_color + "review: ", predictions)
        return {
            "predictions": predictions,
        }
    
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
