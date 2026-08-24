// Mock current-user data. Shape is designed to map 1:1 onto a future
// GET /api/me response — replace this export with a fetch() result later.

export const currentUser = {
  id: 'u_1001',
  name: 'Alex Rivera',
  firstName: 'Alex',
  avatarInitials: 'AR',
  targetRole: 'Frontend Developer',
  currentLevel: 'Beginner–Intermediate',
  careerReadiness: 72, // 0-100
  overallProgress: 34, // 0-100, % of roadmap complete
  streakDays: 6,
  weeklyLearningHours: 8,
  totalLearningHours: 46,
  interests: ['Web Development', 'UI Engineering', 'Design Systems', 'Accessibility'],
  learningStyle: 'Project-based, with short video primers',
  preferredSessionLength: '30–45 min',
  joinedAt: '2026-05-12',
  currentFocus: {
    skillId: 'sk_react',
    label: 'React Fundamentals',
  },
  learningHistory: [
    { id: 'lh_1', title: 'HTML & Semantic Markup', completedAt: '2026-06-02', type: 'course' },
    { id: 'lh_2', title: 'CSS Layout Systems', completedAt: '2026-06-21', type: 'course' },
    { id: 'lh_3', title: 'JavaScript Fundamentals', completedAt: '2026-07-18', type: 'course' },
    { id: 'lh_4', title: 'Personal Portfolio Site', completedAt: '2026-07-25', type: 'project' },
  ],
  learningPreferences: {
    pace: 'Steady (3–5 sessions / week)',
    format: ['Interactive courses', 'Hands-on projects', 'Short assessments'],
    difficulty: 'Push me slightly beyond current level',
  },
  notificationSettings: {
    roadmapUpdates: true,
    weeklyDigest: true,
    assessmentReminders: true,
    productNews: false,
  },
};

export const recentActivity = [
  { id: 'act_1', type: 'assessment', label: 'Completed "JavaScript Fundamentals" assessment', meta: 'Scored 88%', timestamp: '2026-08-22T14:20:00Z' },
  { id: 'act_2', type: 'roadmap', label: 'Roadmap adapted after assessment results', meta: 'State Management added', timestamp: '2026-08-22T14:22:00Z' },
  { id: 'act_3', type: 'course', label: 'Started "React Fundamentals"', meta: '2 of 9 lessons complete', timestamp: '2026-08-23T09:05:00Z' },
  { id: 'act_4', type: 'project', label: 'Submitted "Portfolio Site" project', meta: 'Reviewed · Passed', timestamp: '2026-07-25T18:40:00Z' },
];