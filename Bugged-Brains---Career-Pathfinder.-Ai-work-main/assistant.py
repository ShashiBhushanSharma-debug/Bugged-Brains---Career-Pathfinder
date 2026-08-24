import os
from typing import Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from schemas import LearningRoadmap, LearnerState


class RoadmapQAAssistant:
    """
    Answers ad-hoc learner questions about their roadmap using Groq.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama-3.3-70b-versatile"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.2,
            api_key=api_key or os.getenv("GROQ_API_KEY")
        )

    def answer_query(
        self,
        query: str,
        roadmap: LearningRoadmap,
        learner: LearnerState
    ) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
            You are the LearnPath AI Assistant.
            Explain curriculum decisions and answer queries based strictly on the provided Roadmap and Learner State.
            Be transparent, encouraging, and pedagogically sound.
            """),
            ("human", """
            Learner Goal: {goal}
            Current Mastery Levels: {skills}
            
            Current Active Roadmap:
            {roadmap_json}
            
            Learner Query: {query}
            
            Provide a clear, direct answer explaining the curriculum logic:
            """)
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "goal": learner.target_goal,
            "skills": learner.skills,
            "roadmap_json": roadmap.model_dump_json(indent=2),
            "query": query
        })
        return response.contents