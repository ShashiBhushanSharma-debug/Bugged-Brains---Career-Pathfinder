export const upcomingAssessment = {
  id: 'as_react_basics',
  title: 'React Basics Check-in',
  skill: 'React',
  questionCount: 6,
  estimatedTime: '10 min',
  unlocksIfPassed: 'React State Management',
};

export const assessments = {
  as_react_basics: {
    id: 'as_react_basics',
    title: 'React Basics Check-in',
    skill: 'React',
    estimatedTime: '10 min',
    questions: [
      {
        id: 'q1',
        prompt: 'What does a React component return?',
        options: [
          { id: 'a', text: 'A DOM element only' },
          { id: 'b', text: 'JSX describing what should appear on screen' },
          { id: 'c', text: 'A CSS stylesheet' },
          { id: 'd', text: 'A database query' },
        ],
        correct: 'b',
        skill: 'React',
      },
      {
        id: 'q2',
        prompt: 'How do you pass data from a parent component to a child?',
        options: [
          { id: 'a', text: 'Global variables' },
          { id: 'b', text: 'Props' },
          { id: 'c', text: 'Direct DOM access' },
          { id: 'd', text: 'CSS variables' },
        ],
        correct: 'b',
        skill: 'React',
      },
      {
        id: 'q3',
        prompt: 'Which hook lets a component hold local, changing data?',
        options: [
          { id: 'a', text: 'useEffect' },
          { id: 'b', text: 'useContext' },
          { id: 'c', text: 'useState' },
          { id: 'd', text: 'useRef' },
        ],
        correct: 'c',
        skill: 'State Management',
      },
      {
        id: 'q4',
        prompt: 'What is the recommended way to share state between two sibling components?',
        options: [
          { id: 'a', text: 'Lift the state up to their common parent' },
          { id: 'b', text: 'Use two separate useState calls that stay in sync manually' },
          { id: 'c', text: 'Copy the state into both components' },
          { id: 'd', text: 'Store it in the URL only' },
        ],
        correct: 'a',
        skill: 'State Management',
      },
      {
        id: 'q5',
        prompt: 'What triggers a React component to re-render?',
        options: [
          { id: 'a', text: 'Scrolling the page' },
          { id: 'b', text: 'A change in its state or props' },
          { id: 'c', text: 'Refreshing the browser tab only' },
          { id: 'd', text: 'Editing the CSS file' },
        ],
        correct: 'b',
        skill: 'React',
      },
      {
        id: 'q6',
        prompt: 'Which pattern helps avoid prop-drilling across many nested components?',
        options: [
          { id: 'a', text: 'useState in every component' },
          { id: 'b', text: 'Context API' },
          { id: 'c', text: 'Inline styles' },
          { id: 'd', text: 'Larger component files' },
        ],
        correct: 'b',
        skill: 'State Management',
      },
    ],
  },
};

// A completed result used to populate the results screen after submission.
export function scoreAssessment(assessment, answers) {
  const bySkill = {};
  let correctCount = 0;

  assessment.questions.forEach((q) => {
    const isCorrect = answers[q.id] === q.correct;
    if (isCorrect) correctCount += 1;
    bySkill[q.skill] = bySkill[q.skill] || { correct: 0, total: 0 };
    bySkill[q.skill].total += 1;
    if (isCorrect) bySkill[q.skill].correct += 1;
  });

  const skillPerformance = Object.entries(bySkill).map(([skill, v]) => ({
    skill,
    percent: Math.round((v.correct / v.total) * 100),
  }));

  const strengths = skillPerformance.filter((s) => s.percent >= 70).map((s) => s.skill);
  const weakAreas = skillPerformance.filter((s) => s.percent < 70).map((s) => s.skill);

  return {
    score: Math.round((correctCount / assessment.questions.length) * 100),
    correctCount,
    total: assessment.questions.length,
    skillPerformance,
    strengths,
    weakAreas,
    recommendedNext:
      weakAreas.length > 0
        ? `Reinforce ${weakAreas.join(', ')} before moving on.`
        : 'You are ready to move on to the next roadmap step.',
  };
}