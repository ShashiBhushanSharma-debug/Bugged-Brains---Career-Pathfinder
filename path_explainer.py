import os
from typing import Dict, List, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from schemas import LearnerState, LearningRoadmap


class ExplainablePathGenerator:
    """
    Generates a structured, prerequisite-aware learning roadmap 
    with explicit AI explanations for every milestone using Groq.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: str = "llama-3.3-70b-versatile"):
        self.llm = ChatGroq(
            model=model_name,
            temperature=0.1,
            api_key=api_key or os.getenv("GROQ_API_KEY")
        )
        self.parser = PydanticOutputParser(pydantic_object=LearningRoadmap)

    def generate_roadmap(
        self,
        learner: LearnerState,
        skill_gaps: Dict[str, float],
        dependency_ordered_skills: List[str]
    ) -> LearningRoadmap:
        system_instruction = """
        You are an expert Educational Curriculum Designer and AI Reasoning Architect.
        Your task is to generate a personalized, prerequisite-aware learning roadmap.

        Strict Rules:
        1. Follow the provided prerequisite sequence strictly. Do not place advanced topics before fundamentals.
        2. Incorporate a balanced mix of courses, hands-on projects, and checkpoint assessments.
        3. Every single node MUST contain an explicit, rich 'why_now_explanation' detailing:
           - The exact skill gap being resolved.
           - Why this step must occur at this exact sequence position.
           - How it moves the learner toward their primary career goal.
        4. Calculate total_estimated_weeks based on the learner's weekly available study hours.

        {format_instructions}
        """

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("human", """
            Learner Profile:
            - Learner ID: {learner_id}
            - Target Goal: {target_goal}
            - Current Skill Levels: {current_skills}
            - Weekly Study Hours: {weekly_hours}
            - Preferred Learning Style: {learning_style}
            
            Calculated Skill Gaps (Required - Current):
            {skill_gaps}

            Topologically Ordered Skills to Cover:
            {ordered_skills}

            Generate the complete, fully articulated LearningRoadmap JSON.
            """)
        ])

        chain = prompt | self.llm | self.parser

        return chain.invoke({
            "learner_id": learner.learner_id,
            "target_goal": learner.target_goal,
            "current_skills": learner.skills,
            "weekly_hours": learner.weekly_hours,
            "learning_style": learner.preferred_learning_style,
            "skill_gaps": skill_gaps,
            "ordered_skills": dependency_ordered_skills,
            "format_instructions": self.parser.get_format_instructions()
        })