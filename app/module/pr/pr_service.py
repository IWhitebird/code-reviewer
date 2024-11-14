import asyncio
import json
import logging
from typing import List

from app.module.agents.gemini_agent import GeminiAgent
from app.module.github.gh_service import GHService
from app.module.pr.py_model import File, FileIssue, PRReview, Summary
from app.worker.celery_app import celery_app
from app.db.redis_app import redis_app
from app.module.pr.pr_schema import PRAnalyzeLLMInput , PRAnalyzeLLMOutput
class PRService:
    @staticmethod
    @celery_app.task(name='tasks_analyze_pr')
    def analyze_pr(repo_url : str, pr_number : int, github_token : str) -> str:
        try:
            task_id = celery_app.current_task.request.id
            logging.info(f"Analyzing PR ({task_id} {repo_url}, {pr_number})")
            
            pr_meta = asyncio.run(GHService.get_pr_meta(repo_url, pr_number, github_token))
            pr_files = asyncio.run(GHService.get_pr_files(repo_url, pr_number, github_token))

            # agent = GeminiAgent(input_schema=PRAnalyzeLLMInput , output_schema=PRAnalyzeLLMOutput)
            agent = GeminiAgent()
            
            # Not working properly for Gemini
            agent.model.with_types(input_type=PRAnalyzeLLMInput, output_type=PRAnalyzeLLMOutput)
           
            # Added query workaround cause outputType is not working properly        
            query = """
                Analyze the file content and provide feedback on:
                1. Code style and formatting issues
                2. Potential bugs or errors
                3. Performance improvements

                Format your response as a JSON object with the following structure:`
                {
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
                    }
                }
            """
            
            inputArr : List[PRAnalyzeLLMInput] = []
            
            for files in pr_files:
                inputArr.append(PRAnalyzeLLMInput(
                    query = query, 
                    pr_title = pr_meta['title'] , 
                    file_name = files['filename'] , 
                    file_content = files['patch']
                ))
                
            raw_results = agent.model.batch(inputs=[input.model_dump_json() for input in inputArr])
            
            parsed_results = []
            for result in raw_results:
                try:
                    # First try to parse as JSON directly
                    # If the result contains markdown code fence, extract JSON
                    if isinstance(result, str) and '```json' in result:
                        json_content = result.split('```json\n')[1].split('```')[0]
                        parsed_result = json.loads(json_content)
                    else: 
                        parsed_result = json.loads(result)
                        
                    logging.debug(f"Parsed result: {parsed_result}")
                    parsed_results.append(parsed_result)
                    
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse result as JSON: {e}")
                    logging.debug(f"Problematic result: {result}")
                    continue
                except Exception as e:
                    logging.error(f"Error processing result: {e}")
                    continue
                final_results = PRReview(
                    files=[File(
                            name=res["file"]["name"],
                            issues=[FileIssue(
                                type=issue["type"],
                                line=issue["line_number"],
                                description=issue["description"],
                                suggestion=issue["suggestion"]
                            ) for issue in res["file"]["issues"]]
                        )
                        for res in parsed_results
                    ],
                    summary=Summary(
                        total_files=sum(res['summary']['total_files'] for res in parsed_results),
                        total_issues=sum(res['summary']['total_issues'] for res in parsed_results),
                        critical_issues=sum(res['summary']['critical_issues'] for res in parsed_results)
                    )
                )

            logging.info(f"Saving results to Redis: {final_results}") 
            redis_app.set(
                name=f"{task_id}", 
                value=json.dumps({
                    "task_id": task_id, 
                    "status": "completed", 
                    "results": final_results.model_dump()
                })
            )
            
            pass
        except Exception as e:
            logging.error(f"Unexpected error while analyzing PR with task_id {task_id} : {e}")
            pass
        