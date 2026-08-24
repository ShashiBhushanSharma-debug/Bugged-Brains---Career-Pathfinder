from typing import Tuple
from schemas import LearnerState, LearningRoadmap, AssessmentSignal, RoadmapStep, NodeRationale
from path_explainer import ExplainablePathGenerator


class AdaptiveReplannerEngine:
    """
    Closed-loop adaptive controller that maintains learner state probabilities
    and recalculates the learning graph upon feedback or assessment events.
    """
    def __init__(self, path_generator: ExplainablePathGenerator):
        self.generator = path_generator

    def update_learner_knowledge_state(
        self, 
        learner: LearnerState, 
        signal: AssessmentSignal
    ) -> float:
        """
        Updates the mastery probability P(L_t) of a skill using a Bayesian update rule without numpy.
        """
        prior_mastery = learner.skills.get(signal.target_skill, 0.20)
        
        slip_rate = 0.10
        guess_rate = 0.20
        transit_rate = 0.15

        is_passed = signal.score_percentage >= 65.0

        if is_passed:
            numerator = prior_mastery * (1.0 - slip_rate)
            denominator = numerator + ((1.0 - prior_mastery) * guess_rate)
            posterior_mastery = numerator / max(denominator, 1e-6)
        else:
            numerator = prior_mastery * slip_rate
            denominator = numerator + ((1.0 - prior_mastery) * (1.0 - guess_rate))
            posterior_mastery = numerator / max(denominator, 1e-6)

        updated_mastery = posterior_mastery + ((1.0 - posterior_mastery) * transit_rate)
        final_score = round(max(0.0, min(1.0, updated_mastery)), 4)
        learner.skills[signal.target_skill] = final_score
        return final_score

    def replan_on_assessment(
        self,
        current_roadmap: LearningRoadmap,
        learner: LearnerState,
        signal: AssessmentSignal
    ) -> Tuple[LearningRoadmap, str]:
        # Step 1: Update persistent state
        new_mastery = self.update_learner_knowledge_state(learner, signal)
        
        # Step 2: Filter out completed step
        remaining_steps = [s for s in current_roadmap.steps if s.step_id != signal.step_id]
        
        # Step 3: Handle Failure (<60%)
        if signal.score_percentage < 60.0:
            remedial_step_id = f"remedial_{signal.target_skill.lower().replace(' ', '_')}"
            
            remedial_node = RoadmapStep(
                step_id=remedial_step_id,
                title=f"Targeted Recovery: {signal.target_skill} Core Foundations",
                resource_type="refresher",
                target_skill=signal.target_skill,
                difficulty="beginner",
                estimated_hours=4,
                is_completed=False,
                rationale=NodeRationale(
                    goal_alignment_score=0.98,
                    skill_gap_addressed=f"Critical misconception detected in {signal.target_skill} (Score: {signal.score_percentage}%)",
                    prerequisite_context="Prerequisite enforcement active. Downstream advanced topics temporarily paused.",
                    why_now_explanation=(
                        f"Your assessment score for {signal.target_skill} was {signal.score_percentage}%, which is below the 60% mastery threshold. "
                        f"This targeted refresher reinforces core mechanics before you proceed to downstream dependent projects."
                    )
                )
            )
            remaining_steps.insert(0, remedial_node)
            status_message = f"Remedial intervention injected for '{signal.target_skill}'. Downstream steps held."

        # Step 4: Handle Fast-Track (>=90%)
        elif signal.score_percentage >= 90.0:
            original_len = len(remaining_steps)
            remaining_steps = [
                s for s in remaining_steps
                if not (s.target_skill == signal.target_skill and s.difficulty == "beginner" and s.resource_type == "course")
            ]
            dropped_count = original_len - len(remaining_steps)
            status_message = f"High performance demonstrated ({signal.score_percentage}%). Skipped {dropped_count} redundant beginner module(s)."

        # Step 5: Handle Pacing Feedback
        elif signal.user_feedback and "too fast" in signal.user_feedback.lower():
            for step in remaining_steps:
                step.estimated_hours = int(step.estimated_hours * 1.5)
            status_message = "Pacing constraint acknowledged: increased estimated allocations across remaining steps."
        else:
            status_message = "Progress recorded successfully. Roadmap sequencing unchanged."

        current_roadmap.steps = remaining_steps
        current_roadmap.milestone_count = len(remaining_steps)
        
        return current_roadmap, status_message