from schemas import LearnerState, AssessmentSignal
from path_explainer import ExplainablePathGenerator
from adaptive_engine import AdaptiveReplannerEngine
from assistant import RoadmapQAAssistant


def run_demo():
    print("================================================================")
    print("  AI-POWERED PERSONALIZED LEARNING PATH RECOMMENDER (GROQ)")
    print("================================================================\n")

    initial_learner = LearnerState(
        learner_id="L-9042",
        target_goal="Machine Learning Engineer",
        skills={
            "Python": 0.85,
            "Linear Algebra": 0.30,
            "Probability & Statistics": 0.35,
            "Classical ML": 0.40,
            "Deep Learning": 0.10
        },
        weekly_hours=10,
        preferred_learning_style="project_based"
    )

    skill_gaps = {
        "Linear Algebra": 0.45,
        "Probability & Statistics": 0.40,
        "Classical ML": 0.35,
        "Deep Learning": 0.65
    }

    dependency_order = [
        "Linear Algebra",
        "Probability & Statistics",
        "Classical ML",
        "Deep Learning"
    ]

    print("[STEP 1] Calling Groq API to Generate Explainable Roadmap...")
    explainer = ExplainablePathGenerator()
    replanner = AdaptiveReplannerEngine(path_generator=explainer)
    assistant = RoadmapQAAssistant()

    initial_roadmap = explainer.generate_roadmap(
        learner=initial_learner,
        skill_gaps=skill_gaps,
        dependency_ordered_skills=dependency_order
    )

    print(f"\nGenerated {len(initial_roadmap.steps)} Sequential Milestones:")
    for idx, step in enumerate(initial_roadmap.steps, 1):
        print(f"\n  {idx}. [{step.resource_type.upper()}] {step.title} ({step.estimated_hours} hrs)")
        print(f"     Target Skill : {step.target_skill} | Difficulty: {step.difficulty}")
        print(f"     Why Now?     : {step.rationale.why_now_explanation}")

    tested_step = initial_roadmap.steps[0]
    print("\n----------------------------------------------------------------")
    print(f"[STEP 2] Simulating Learner Assessment for: '{tested_step.title}'")
    print("         Score: 42.0% (Failure) | Feedback: 'Struggled with matrix transformations'")
    print("----------------------------------------------------------------")

    failure_signal = AssessmentSignal(
        step_id=tested_step.step_id,
        target_skill=tested_step.target_skill,
        score_percentage=42.0,
        user_feedback="Struggled with matrix transformations"
    )

    updated_roadmap, log_message = replanner.replan_on_assessment(
        current_roadmap=initial_roadmap,
        learner=initial_learner,
        signal=failure_signal
    )

    print(f"\n[REPLANNER TRIGGERED] {log_message}")
    print(f"Updated Mastery in '{tested_step.target_skill}': {initial_learner.skills[tested_step.target_skill] * 100:.1f}%")
    
    next_action = updated_roadmap.steps[0]
    print(f"\nImmediate Next Action is Now:")
    print(f"  --> [{next_action.resource_type.upper()}] {next_action.title}")
    print(f"      Rationale: {next_action.rationale.why_now_explanation}")

    print("\n----------------------------------------------------------------")
    print("[STEP 3] Testing Roadmap Q&A Assistant")
    print("----------------------------------------------------------------")
    query = "Why was a remedial step added instead of moving forward?"
    answer = assistant.answer_query(query=query, roadmap=updated_roadmap, learner=initial_learner)
    print(f"User: {query}")
    print(f"Assistant: {answer}\n")


if __name__ == "__main__":
    run_demo()