// Skill inventory: current proficiency vs. what the target role requires.
// proficiency / required are 0-100. `category` groups skills into the
// four buckets shown on the Skill Analysis screen.

export const targetRole = {
  title: 'Frontend Developer',
  description: 'Builds accessible, performant user interfaces and owns the client-side layer of a product.',
};

export const skills = [
  {
    id: 'sk_html',
    name: 'HTML',
    proficiency: 92,
    required: 80,
    category: 'known',
    status: 'completed',
    reasoning: ['Completed "HTML & Semantic Markup"', 'Used in 3 projects since'],
  },
  {
    id: 'sk_css',
    name: 'CSS',
    proficiency: 85,
    required: 80,
    category: 'known',
    status: 'completed',
    reasoning: ['Completed "CSS Layout Systems"', 'Strong grasp of Flexbox & Grid'],
  },
  {
    id: 'sk_js',
    name: 'JavaScript',
    proficiency: 80,
    required: 85,
    category: 'known',
    status: 'completed',
    reasoning: ['Completed "JavaScript Fundamentals"', 'Scored 88% on latest assessment'],
  },
  {
    id: 'sk_react',
    name: 'React',
    proficiency: 28,
    required: 85,
    category: 'developing',
    status: 'current',
    reasoning: [
      'Target role requires React',
      'Current proficiency: Beginner',
      'JavaScript prerequisite: Completed',
    ],
  },
  {
    id: 'sk_state',
    name: 'State Management',
    proficiency: 10,
    required: 70,
    category: 'developing',
    status: 'adapted',
    reasoning: [
      'Assessment showed a gap in component state patterns',
      'Required before advanced React work',
      'Added to roadmap after your last assessment',
    ],
  },
  {
    id: 'sk_ts',
    name: 'TypeScript',
    proficiency: 15,
    required: 65,
    category: 'recommended',
    status: 'recommended',
    reasoning: [
      'Most Frontend Developer roles list TypeScript',
      'Builds directly on your JavaScript foundation',
      'Unlocks 2 further roadmap skills',
    ],
  },
  {
    id: 'sk_testing',
    name: 'Testing',
    proficiency: 0,
    required: 55,
    category: 'recommended',
    status: 'locked',
    reasoning: [
      'Missing entirely from current skill set',
      'Required for production-quality roadmap milestone',
      'Unlocked once React & State Management are further along',
    ],
  },
  {
    id: 'sk_a11y',
    name: 'Accessibility',
    proficiency: 20,
    required: 60,
    category: 'future',
    status: 'locked',
    reasoning: ['Listed as an interest area', 'Recommended after core React skills solidify'],
  },
  {
    id: 'sk_perf',
    name: 'Web Performance',
    proficiency: 5,
    required: 50,
    category: 'future',
    status: 'locked',
    reasoning: ['Advanced topic, scheduled after project milestone'],
  },
  {
    id: 'sk_design_systems',
    name: 'Design Systems',
    proficiency: 12,
    required: 45,
    category: 'future',
    status: 'locked',
    reasoning: ['Matches your stated interest in Design Systems'],
  },
];

export const skillCategories = [
  { id: 'known', label: 'You already know', description: 'Meets or exceeds the bar for your target role.' },
  { id: 'developing', label: 'Currently developing', description: 'In active progress on your roadmap right now.' },
  { id: 'recommended', label: 'Recommended next', description: 'Highest-leverage skills to pick up next.' },
  { id: 'future', label: 'Future skills', description: 'Scheduled later, once prerequisites are in place.' },
];