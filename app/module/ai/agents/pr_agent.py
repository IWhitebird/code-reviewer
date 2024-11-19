import asyncio
import json
import logging
import ollama
from typing import Any, List, TypedDict

from redis import Redis
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.agents import AgentAction
from semantic_router.utils.function_call import FunctionSchema

from app.module.ai.agents.base_agent import AgentState, AgentAction
from app.module.github.gh_service import GHService
from app.module.ai.llm.ollama_llm import OllamaLLM
from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles

from app.module.ai.knowledge.internet_search import InternetSearch
from app.module.ai.knowledge.repo_tree import RepoTree
from app.module.pr.pr_model import File


class PRAgent():
    def __init__(self, gh : GHService , repo_url: str , cache : Redis):
        """
        Initialize the agent with a GitHub Instance.
        """
        self.gh = gh
        self.repo_url = repo_url
        self.repo_tree = RepoTree(gh, cache, repo_url)
        self.internet_search = InternetSearch(search_engine="google")
        self.memory_saver = MemorySaver()
        self.tools = [
            # self.repo_search_tool,
            self.web_search_tool,
            self.repo_file_tree_structure_tool,
            self.repo_file_content_tool,
            self.final_answer_tool,
        ]
        self.to_ollama = []
        self.workflow = None
        self.ollama = OllamaLLM()

        self._register_tool()
        self._build_workflow()

    def get_pr_review(self , pr_number: int):
        """
        Get the PR review for the given PR number.
        """
        pr_files = self.gh.get_pr_files(self.repo_url, pr_number)
        print("Calling the agent for each file in the PR")

        result = []
        path_and_content = []
        for file in pr_files.get_files():
            if file.patch:
                file_content = file.patch.replace("\n", " ")
                file_path = file.filename.replace("\n", " ")
                path_and_content.append((file_path, file_content))
                agent_response = self.get_agent_response_for_file(file_path, file_content)
                result.append(agent_response)
        # TO SLOW TO RUN IN PARALLEL
        # result = self.get_agent_response_for_file_parallel(path_and_content)
        return result

    def get_agent_response_for_file(self , file_path : str , file_content : str):
        """
            Get the agent response for the given file.
        """
        agent_response = self.workflow.invoke({
                "input": f"""
                    file_path: {file_path}
                    file_content: {file_content}
                """,
                "chat_history": [],
                "intermediate_steps": []
         })
        return agent_response


    def get_agent_response_for_file_parallel(self , path_and_content : List[tuple[str, str]]) -> str:
        """
            Get the agent response for the given file.
        """
        agent_response = self.workflow.batch(
            [{
                "input": f"""
                    file_path: {file_path}
                    file_content: {file_content}
                """,
                "chat_history": [],
                "intermediate_steps": []
            } for file_path, file_content in path_and_content]
        )
        return agent_response


    def web_search_tool(self , query: str) -> list[str]:
        """
            Call to search the web for information.
            input for this tool -> (query of type string)
        """
        try:
            result = self.internet_search.search(query)
            return result
        except Exception as e:
            logging.error(f"Error in web_search_tool: {e}")
            return ["web_search_tool currenly not working don't use this tool again"]

    def repo_file_tree_structure_tool(self) -> str:
        """
            Returns the tree structure of the repository.
            input for this tool -> (no input needed)
        """
        try:
            result = self.repo_tree.get_tree_readable_for_llm()
            return result
        except Exception as e:
            logging.error(f"Error in repo_file_tree_structure_tool: {e}")
            return "repo_file_tree_structure_tool currenly not working don't use this tool again"

    def final_answer_tool(self , file , summary) -> Any:
        """
        Returns a natural language response to the user. There are four sections
        to be returned to the user, those are:
        input of this tool is a of the following format:
        "file": {
            "name": "filename" in string,
            "issues": [{
                "type": "issue type" in string,
                "description": "detailed description" in string,
                "line_number": "line number" in integer,
                "suggestion": "suggested fix" in string
            }]
        },

        "summary": {
            "total_files": total_files in integer,
            "total_issues": total_issues in integer,
                "critical_issues": critical_issues in integer
        """
        return {"file":file , "summary":summary}

    def repo_file_content_tool(self , file_path: str) -> str:
        """
            Call this tool when you want to get the entire content of a file.
            input for this tool -> (file_path of type string)
        """
        try:
            result = self.repo_tree.get_file_content(file_path)
            return result
        except Exception as e:
            logging.error(f"Error in repo_file_content_tool: {e}")
            return "repo_file_content_tool currenly not working don't use this tool again"

    def _register_tool(self):
        # self.search_schema = FunctionSchema(search).to_ollama()
        # self.final_answer_schema = FunctionSchema(final_answer).to_ollama()
        # self.tool_str_to_func = {
        #     "search": search,
        #     "final_answer": final_answer
        # }
        self.web_search_schema = FunctionSchema(self.web_search_tool).to_ollama()
        # self.repo_search_schema = FunctionSchema(self.repo_search_tool).to_ollama()
        self.repo_file_tree_structure_schema = FunctionSchema(self.repo_file_tree_structure_tool).to_ollama()
        self.repo_file_content_schema = FunctionSchema(self.repo_file_content_tool).to_ollama()
        self.final_answer_schema = FunctionSchema(self.final_answer_tool).to_ollama()

        self.to_ollama = [
            self.web_search_schema,
            self.repo_file_tree_structure_schema,
            self.repo_file_content_schema,
            self.final_answer_schema,
            # self.repo_search_schema,
        ]

        self.tool_str_to_func = {
            "web_search_tool": self.web_search_tool,
        #   "repo_search": self.repo_search_tool,
            "repo_file_tree_structure_tool": self.repo_file_tree_structure_tool,
            "repo_file_content_tool": self.repo_file_content_tool,
            "final_answer_tool": self.final_answer_tool
        }

    def _build_workflow(self):
        try:
            graph = StateGraph(AgentState)
            graph.add_node("oracle", self._run_oracle)

            graph.add_node("web_search_tool", self._run_tool)
            # graph.add_node("search_repo_tool", self._run_tool)
            graph.add_node("repo_file_tree_structure_tool", self._run_tool)
            graph.add_node("repo_file_content_tool", self._run_tool)
            graph.add_node("final_answer_tool", self._run_tool)

            graph.set_entry_point("oracle")
            graph.add_conditional_edges(source="oracle",path=self._router)

            for tool_obj in self.to_ollama:
                tool_name = tool_obj["function"]["name"]
                if tool_name != "final_answer_tool":
                    graph.add_edge(tool_name, "oracle")  # ————————>
            graph.add_edge("final_answer_tool", END)

            # runnable = graph.compile(checkpointer=self.memory_saver)
            runnable = graph.compile()
            
            self.workflow = runnable
            pass
        except Exception as e:
            logging.error(f"Error in _build_workflow: {e}")
            pass

    def _get_system_prompt(self):
        """
            Get the system prompt for the oracle.
        """
        system_prompt = """
            You are an AI Github Pull Request Code Review Assistant tasked with performing comprehensive static analysis on git commit diffs. 
            Your objective is to provide detailed, actionable insights across multiple dimensions of code quality.

            For each git commit diff, systematically evaluate and report on:
                1. Code style and formatting issues
                2. Potential bugs or errors
                3. Performance improvements
            
            There are some tools available to you to help you with this task. 
            You can use these tools to help you find the information you need to answer the user query.
            Tools:
                Strict Note, When using a tool, you provide the tool name and the arguments to use
                in JSON format. For each call, you MUST ONLY use one tool AND the response
                format must ALWAYS be in the pattern:

                ```json
                    {
                        "name": "<tool_name>",
                        "parameters": {"<tool_input_key>": <tool_input_value>}

                    }
                ```

            Remember, NEVER use the any tool more than once.After using the search tool you must summarize your findings with the
            final_answer_tool.
        """
        return system_prompt

    def _get_system_tools_prompt(self):
        """
            Get the system prompt for the tools.
        """
        tools_str = "\n".join([str(tool) for tool in self.to_ollama])

        return (
            f"{self._get_system_prompt()}\n\n"
            f"You can strictly only use the following tools:\n{tools_str}"
        )

    def _create_scratchpad(self ,intermediate_steps: list[AgentAction]):
        """
            Create a scratchpad of the intermediate steps.
        """
        intermediate_steps = [action for action in intermediate_steps if action.tool_output is not None]
        scratch_pad_messages = []
        for action in intermediate_steps:
            scratch_pad_messages.extend(self._action_to_message(action))
        return scratch_pad_messages

    def _action_to_message(self ,action: AgentAction):
        """
            Convert an AgentAction into a list of messages that can be sent to the LLM.
        """
        assistant_content = json.dumps({"name": action.tool_name, "parameters": action.tool_input})
        assistant_message = {"role": "assistant", "content": assistant_content}
        user_message = {"role": "user", "content": action.tool_output}
        return [assistant_message, user_message]

    def _call_llm(self ,user_input: str, chat_history: list[dict], intermediate_steps: list[AgentAction]) -> AgentAction:
        # format the intermediate steps into a scratchpad
        scratchpad = self._create_scratchpad(intermediate_steps)

        # if the scratchpad is not empty, we add a small reminder message to the agent
        if scratchpad:
            tools_used = [action.tool_name for action in intermediate_steps]
            scratchpad += [{
                "role": "user",
                "content": (
                    f"""Please continue, as a reminder my query was '{user_input}'.
                    Only answer to the original query, and nothing else — but use the
                    information I provided to you to do so
                    dont use the following tools : {tools_used}
                    """
                )
            }]

        messages = [
            {"role": "system", "content": self._get_system_tools_prompt()},
            *chat_history,
            {"role": "user", "content": user_input},
            *scratchpad,
        ]
        print("#LLM_CALL : ", messages)
        res = ollama.chat(
            model="llama3.1",
            messages=messages,
            format="json",
            options={"num_ctx" : 1000}
        )

        # res = self.ollama.get_ollama_ollama(
        #     messages=messages,
        #     format="json",
        # )

        return AgentAction.from_ollama(res)

    def _run_oracle(self , state: TypedDict): # type: ignore
        print(f"Running the oracle")
        chat_history = state["chat_history"]
        out = self._call_llm(
            user_input=state["input"],
            chat_history=chat_history,
            intermediate_steps=state["intermediate_steps"]
        )
        return {
            "intermediate_steps": [out]
        }

    def _router(self, state: TypedDict): # type: ignore
        # return the tool name to use
        try:
            if isinstance(state["intermediate_steps"], list):
                return state["intermediate_steps"][-1].tool_name
            else:
                # if we output bad format go to final answer
                print("Router invalid format")
                return "final_answer_tool"
        except Exception as e:
            print("Router error", e)
            return "final_answer_tool"

    def _run_tool(self,state: TypedDict): # type: ignore
        tool_name = state["intermediate_steps"][-1].tool_name
        tool_args = state["intermediate_steps"][-1].tool_input
        print(f"run_tool | {tool_name}.invoke(input={tool_args})")
        out = self.tool_str_to_func[tool_name](**tool_args)
        action_out = AgentAction(
            tool_name=tool_name,
            tool_input=tool_args,
            tool_output=str(out),
        )
        if tool_name == "final_answer_tool":
            return {"output": out}
        else:
            return {"intermediate_steps": [action_out]}
    
    def get_graph(self):
        self.workflow.get_graph().draw_mermaid_png(
            curve_style=CurveStyle.LINEAR,
            node_colors=NodeStyles(first="#ffdfba", last="#baffc9", default="#fad7de"),
            wrap_label_n_words=9,
            output_file_path="/home/blade/projects/python/code-reviewer/workflow.png",
            draw_method=MermaidDrawMethod.API,
            background_color="white",
            padding=10, 
        )
        pass
