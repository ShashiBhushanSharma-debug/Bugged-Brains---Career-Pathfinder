-- =============================================================================
-- Migration: 002_seed_data.sql
-- Project:   Career Pathfinder — Supabase PostgreSQL
-- Phase:     1 (Seed data only — derived from frontend mock files)
-- Author:    Sanchit (DB/Backend module)
-- Created:   2026-08-25
--
-- Source of truth for all values:
--   - frontend/src/data/skillsData.js   -> skills, career_skills, skill_prerequisites
--   - frontend/src/data/coursesData.js  -> resources, resource_skills
--   - frontend/src/data/roadmapData.js  -> roadmap_nodes, roadmap_node_prerequisites
--   - frontend/src/data/assessmentData.js -> assessments, assessment_questions
--   - frontend/src/data/userData.js     -> learner_profiles, learner_skills,
--                                          learning_history, learner_roadmap_nodes,
--                                          activity_log, roadmap_replans
--
-- Seed insert order (respects FK dependencies):
--   1.  skills
--   2.  careers
--   3.  career_skills
--   4.  skill_prerequisites
--   5.  resources
--   6.  resource_skills
--   7.  roadmap_nodes
--   8.  roadmap_node_prerequisites
--   9.  assessments
--   10. assessment_questions
--   11. learner_profiles
--   12. learner_skills
--   13. learning_history
--   14. learner_roadmap_nodes
--   15. activity_log
--   16. roadmap_replans
--   17. recommendations (seeded from mock recommended=true resources)
-- =============================================================================


-- =============================================================================
-- 1. SKILLS
-- Source: skillsData.js skills[] array
-- Note: proficiency and required scores are NOT seeded here — they belong
--       in learner_skills and career_skills respectively.
-- =============================================================================
INSERT INTO skills (id, name, description) VALUES
    ('sk_html',           'HTML',             'Structural markup and semantic HTML for web interfaces.'),
    ('sk_css',            'CSS',              'Visual layer, layout systems, Flexbox and Grid.'),
    ('sk_js',             'JavaScript',       'Core programming layer for web: DOM, async, ES6+.'),
    ('sk_react',          'React',            'Component-based UI development using the React library.'),
    ('sk_state',          'State Management', 'useState, useReducer, lifting state, Context API patterns.'),
    ('sk_ts',             'TypeScript',       'Static typing for JavaScript: typed components, props, and hooks.'),
    ('sk_testing',        'Testing',          'Unit testing components and integration test basics.'),
    ('sk_a11y',           'Accessibility',    'Building inclusive, ARIA-compliant, keyboard-navigable interfaces.'),
    ('sk_perf',           'Web Performance',  'Core Web Vitals, rendering optimisation, and load performance.'),
    ('sk_design_systems', 'Design Systems',   'Component libraries, design tokens, and systematic UI consistency.')
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 2. CAREERS
-- Source: skillsData.js targetRole object
-- =============================================================================
INSERT INTO careers (id, title, description) VALUES
    (
        'career_frontend_dev',
        'Frontend Developer',
        'Builds accessible, performant user interfaces and owns the client-side layer of a product.'
    )
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 3. CAREER SKILLS
-- Source: skillsData.js skills[].required values for 'Frontend Developer'
-- =============================================================================
INSERT INTO career_skills (career_id, skill_id, required_score, importance) VALUES
    ('career_frontend_dev', 'sk_html',           80, 'core'),
    ('career_frontend_dev', 'sk_css',            80, 'core'),
    ('career_frontend_dev', 'sk_js',             85, 'core'),
    ('career_frontend_dev', 'sk_react',          85, 'core'),
    ('career_frontend_dev', 'sk_state',          70, 'core'),
    ('career_frontend_dev', 'sk_ts',             65, 'nice-to-have'),
    ('career_frontend_dev', 'sk_testing',        55, 'nice-to-have'),
    ('career_frontend_dev', 'sk_a11y',           60, 'nice-to-have'),
    ('career_frontend_dev', 'sk_perf',           50, 'nice-to-have'),
    ('career_frontend_dev', 'sk_design_systems', 45, 'nice-to-have')
ON CONFLICT (career_id, skill_id) DO NOTHING;


-- =============================================================================
-- 4. SKILL PREREQUISITES
-- Source: skillsData.js skills[].reasoning[] + roadmapData.js
-- Each prerequisite edge is explicitly supported by the mock reasoning text.
-- =============================================================================
INSERT INTO skill_prerequisites (skill_id, prerequisite_skill_id) VALUES
    -- React: "JavaScript prerequisite: Completed" (skillsData.js sk_react reasoning)
    ('sk_react',          'sk_js'),
    -- State Management: "Required before advanced React work" (sk_state reasoning)
    ('sk_state',          'sk_react'),
    -- TypeScript: "Builds directly on your JavaScript foundation" (sk_ts reasoning)
    ('sk_ts',             'sk_js'),
    -- Testing: "Unlocked once React & State Management are further along" (sk_testing reasoning)
    ('sk_testing',        'sk_react'),
    ('sk_testing',        'sk_state'),
    -- Accessibility: "Recommended after core React skills solidify" (sk_a11y reasoning)
    ('sk_a11y',           'sk_html'),
    ('sk_a11y',           'sk_react'),
    -- Web Performance: "Advanced topic, scheduled after project milestone" (sk_perf reasoning)
    ('sk_perf',           'sk_react'),
    -- Design Systems: "Matches interest in Design Systems" — requires layout foundation
    ('sk_design_systems', 'sk_css'),
    ('sk_design_systems', 'sk_react')
ON CONFLICT (skill_id, prerequisite_skill_id) DO NOTHING;


-- =============================================================================
-- 5. RESOURCES
-- Source: coursesData.js resources[] array
-- progress and status are NOT seeded here (they are per-learner in learning_history).
-- recommended and whyRecommended are per-learner (seeded in recommendations).
-- =============================================================================
INSERT INTO resources (id, title, description, type, difficulty, duration_text, why_recommended_template) VALUES
    (
        'res_1',
        'React Fundamentals',
        'Learn components, props, hooks, and the React rendering model through hands-on lessons.',
        'course', 'Intermediate', '3 wks',
        'Directly continues from your completed JavaScript course and is required for your target role.'
    ),
    (
        'res_2',
        'State Management in React',
        'useState, useReducer, lifting state up, and an introduction to Context.',
        'course', 'Intermediate', '2 wks',
        'Added after your assessment revealed a state-management gap.'
    ),
    (
        'res_3',
        'Thinking in React (react.dev)',
        'The official guide to structuring component trees before writing code.',
        'documentation', 'Beginner', '20 min',
        'Referenced companion reading for React Fundamentals.'
    ),
    (
        'res_4',
        'CSS Grid in 15 Minutes',
        'A quick refresher on Grid template areas and auto-placement.',
        'video', 'Beginner', '15 min',
        'Supplementary — you have already met the CSS proficiency bar.'
    ),
    (
        'res_5',
        'Task Board — Mini Project',
        'Build a drag-and-drop task board using component state and lifting state up.',
        'project', 'Intermediate', '1 wk',
        'Applies state management immediately after you learn it.'
    ),
    (
        'res_6',
        'TypeScript for React Developers',
        'Add static typing to components, props, and hooks.',
        'course', 'Intermediate', '2 wks',
        'Scheduled after your Task Board project.'
    ),
    (
        'res_7',
        'Writing Your First Unit Test',
        'A short, practical introduction to unit testing philosophy.',
        'article', 'Beginner', '10 min',
        'Primer for the Testing module later on your roadmap.'
    ),
    (
        'res_8',
        'Component Design Practice Set',
        '12 short exercises decomposing UIs into components and props.',
        'practice', 'Intermediate', '30 min',
        'Reinforces concepts from React Fundamentals as you go.'
    )
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 6. RESOURCE SKILLS
-- Source: coursesData.js resources[].skill field
-- Mock has one skill per resource. is_primary = TRUE for all seed rows.
-- =============================================================================
INSERT INTO resource_skills (resource_id, skill_id, is_primary) VALUES
    ('res_1', 'sk_react',   TRUE),
    ('res_2', 'sk_state',   TRUE),
    ('res_3', 'sk_react',   TRUE),
    ('res_4', 'sk_css',     TRUE),
    ('res_5', 'sk_react',   TRUE),
    ('res_5', 'sk_state',   FALSE),  -- Task Board reinforces both React + State Management
    ('res_6', 'sk_ts',      TRUE),
    ('res_6', 'sk_react',   FALSE),  -- TypeScript course also covers typed React components
    ('res_7', 'sk_testing', TRUE),
    ('res_8', 'sk_react',   TRUE)
ON CONFLICT (resource_id, skill_id) DO NOTHING;


-- =============================================================================
-- 7. ROADMAP NODES
-- Source: roadmapData.js roadmapNodes[] array
-- status is NOT seeded here (per-learner, in learner_roadmap_nodes).
-- prerequisites are NOT seeded here (in roadmap_node_prerequisites).
-- =============================================================================
INSERT INTO roadmap_nodes (id, type, title, skill_id, career_id, stage, difficulty, duration_text, description, expected_outcome, skills_gained, why, resources_display) VALUES
    (
        'rm_html', 'skill', 'HTML', 'sk_html', 'career_frontend_dev',
        0, 'Beginner', '1 wk',
        'Structural foundation for every interface you will build.',
        NULL,
        '["Semantic markup", "Forms & accessibility basics"]',
        '["Prerequisite for CSS and JavaScript", "Already completed with strong retention"]',
        '["MDN: HTML Basics", "Course: HTML & Semantic Markup"]'
    ),
    (
        'rm_css', 'skill', 'CSS', 'sk_css', 'career_frontend_dev',
        0, 'Beginner', '2 wks',
        'Visual layer and layout systems used across all roadmap projects.',
        NULL,
        '["Flexbox & Grid", "Responsive layout"]',
        '["Required before component styling in React", "Already completed"]',
        '["Course: CSS Layout Systems"]'
    ),
    (
        'rm_js', 'skill', 'JavaScript', 'sk_js', 'career_frontend_dev',
        1, 'Intermediate', '4 wks',
        'Core programming layer every later skill on this path builds on.',
        NULL,
        '["DOM manipulation", "Async programming", "ES6+ syntax"]',
        '["Prerequisite for React", "Assessment score: 88%"]',
        '["Course: JavaScript Fundamentals"]'
    ),
    (
        'rm_react', 'course', 'React Fundamentals', 'sk_react', 'career_frontend_dev',
        2, 'Intermediate', '3 wks',
        'Component-based UI development — the primary skill your target role requires.',
        'Build and reason about component trees confidently.',
        '["Components & props", "Hooks basics", "Rendering model"]',
        '["You have completed JavaScript fundamentals", "React is required for your target role", "Your current React proficiency is beginner", "It unlocks 4 future roadmap skills"]',
        '["Interactive course: React Fundamentals", "Docs: react.dev — Thinking in React"]'
    ),
    (
        'rm_state', 'skill', 'React State Management', 'sk_state', 'career_frontend_dev',
        3, 'Intermediate', '2 wks',
        'Added after your last assessment revealed a state-management gap.',
        NULL,
        '["useState/useReducer patterns", "Lifting state up", "Context basics"]',
        '["Assessment showed strong React fundamentals", "But identified a gap in state management specifically", "Blocking further progress on real-world components"]',
        '["Course: State Management in React", "Guide: Choosing state patterns"]'
    ),
    (
        'rm_project_1', 'project', 'Mini Project — Task Board', 'sk_react', 'career_frontend_dev',
        4, 'Intermediate', '1 wk',
        'Small drag-and-drop task board to apply state management in a realistic UI.',
        NULL,
        '["Applied component design", "State in a real UI"]',
        '["Reinforces state management immediately after learning it", "Portfolio-ready deliverable"]',
        '["Project brief: Task Board"]'
    ),
    (
        'rm_ts', 'skill', 'TypeScript', 'sk_ts', 'career_frontend_dev',
        5, 'Intermediate', '2 wks',
        'Adds type safety across your components and app logic.',
        NULL,
        '["Static typing", "Typed React components"]',
        '["Listed on most Frontend Developer job requirements", "Builds directly on your JavaScript base"]',
        '["Course: TypeScript for React Developers"]'
    ),
    (
        'rm_project_2', 'project', 'Capstone — Career Dashboard UI', NULL, 'career_frontend_dev',
        6, 'Advanced', '2 wks',
        'A full typed React feature build — the centerpiece of your portfolio.',
        NULL,
        '["End-to-end feature build", "Typed component architecture"]',
        '["Combines every roadmap skill so far into one deliverable"]',
        '["Project brief: Career Dashboard UI"]'
    ),
    (
        'rm_testing', 'skill', 'Testing', 'sk_testing', 'career_frontend_dev',
        7, 'Intermediate', '2 wks',
        'Confidence that your components behave correctly as they grow.',
        NULL,
        '["Unit testing components", "Integration test basics"]',
        '["Currently missing from your skill set entirely", "Expected for production-level roles"]',
        '["Course: Testing React Applications"]'
    ),
    (
        'rm_assessment', 'assessment', 'Frontend Readiness Assessment', NULL, 'career_frontend_dev',
        8, 'Comprehensive', '45 min',
        'Final checkpoint validating readiness for Frontend Developer roles.',
        NULL,
        '["Verified role readiness"]',
        '["Confirms mastery across the full roadmap before you apply"]',
        '[]'
    )
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 8. ROADMAP NODE PREREQUISITES
-- Source: roadmapData.js roadmapNodes[].prerequisites arrays
-- =============================================================================
INSERT INTO roadmap_node_prerequisites (node_id, prerequisite_node_id) VALUES
    -- rm_js requires HTML and CSS
    ('rm_js',         'rm_html'),
    ('rm_js',         'rm_css'),
    -- rm_react requires JavaScript
    ('rm_react',      'rm_js'),
    -- rm_state requires React Fundamentals
    ('rm_state',      'rm_react'),
    -- rm_project_1 requires State Management
    ('rm_project_1',  'rm_state'),
    -- rm_ts requires the Task Board project
    ('rm_ts',         'rm_project_1'),
    -- rm_project_2 requires TypeScript
    ('rm_project_2',  'rm_ts'),
    -- rm_testing requires Capstone project
    ('rm_testing',    'rm_project_2'),
    -- rm_assessment requires Testing
    ('rm_assessment', 'rm_testing')
ON CONFLICT (node_id, prerequisite_node_id) DO NOTHING;


-- =============================================================================
-- 9. ASSESSMENTS
-- Source: assessmentData.js upcomingAssessment + assessments object
-- unlocks_node_id: 'as_react_basics' unlocks 'rm_state' (unlocksIfPassed field)
-- =============================================================================
INSERT INTO assessments (id, title, skill_id, estimated_time, unlocks_node_id) VALUES
    (
        'as_react_basics',
        'React Basics Check-in',
        'sk_react',
        '10 min',
        'rm_state'              -- Unlocks React State Management node on pass
    )
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 10. ASSESSMENT QUESTIONS
-- Source: assessmentData.js assessments.as_react_basics.questions[]
-- Note: IDs are prefixed with assessment ID to guarantee global uniqueness.
-- skill_id per question enables per-skill diagnostic scoring (scoreAssessment pattern).
-- =============================================================================
INSERT INTO assessment_questions (id, assessment_id, prompt, options, correct_option_id, skill_id, order_index) VALUES
    (
        'as_react_basics_q1',
        'as_react_basics',
        'What does a React component return?',
        '[{"id":"a","text":"A DOM element only"},{"id":"b","text":"JSX describing what should appear on screen"},{"id":"c","text":"A CSS stylesheet"},{"id":"d","text":"A database query"}]',
        'b', 'sk_react', 1
    ),
    (
        'as_react_basics_q2',
        'as_react_basics',
        'How do you pass data from a parent component to a child?',
        '[{"id":"a","text":"Global variables"},{"id":"b","text":"Props"},{"id":"c","text":"Direct DOM access"},{"id":"d","text":"CSS variables"}]',
        'b', 'sk_react', 2
    ),
    (
        'as_react_basics_q3',
        'as_react_basics',
        'Which hook lets a component hold local, changing data?',
        '[{"id":"a","text":"useEffect"},{"id":"b","text":"useContext"},{"id":"c","text":"useState"},{"id":"d","text":"useRef"}]',
        'c', 'sk_state', 3
    ),
    (
        'as_react_basics_q4',
        'as_react_basics',
        'What is the recommended way to share state between two sibling components?',
        '[{"id":"a","text":"Lift the state up to their common parent"},{"id":"b","text":"Use two separate useState calls that stay in sync manually"},{"id":"c","text":"Copy the state into both components"},{"id":"d","text":"Store it in the URL only"}]',
        'a', 'sk_state', 4
    ),
    (
        'as_react_basics_q5',
        'as_react_basics',
        'What triggers a React component to re-render?',
        '[{"id":"a","text":"Scrolling the page"},{"id":"b","text":"A change in its state or props"},{"id":"c","text":"Refreshing the browser tab only"},{"id":"d","text":"Editing the CSS file"}]',
        'b', 'sk_react', 5
    ),
    (
        'as_react_basics_q6',
        'as_react_basics',
        'Which pattern helps avoid prop-drilling across many nested components?',
        '[{"id":"a","text":"useState in every component"},{"id":"b","text":"Context API"},{"id":"c","text":"Inline styles"},{"id":"d","text":"Larger component files"}]',
        'b', 'sk_state', 6
    )
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 11. LEARNER PROFILES
-- Source: userData.js currentUser object
-- avatarInitials: NOT stored (derived on client from name).
-- careerReadiness/overallProgress: seeded from mock cached values.
-- =============================================================================
INSERT INTO learner_profiles (
    id, name, first_name, target_career_id, current_level,
    career_readiness, overall_progress, streak_days,
    weekly_learning_hours, total_learning_hours,
    interests, learning_style, preferred_session_length,
    learning_preferences, notification_settings,
    current_focus_skill_id, joined_at
) VALUES (
    'u_1001',
    'Alex Rivera',
    'Alex',
    'career_frontend_dev',
    'Beginner-Intermediate',
    72,
    34,
    6,
    8,
    46,
    ARRAY['Web Development', 'UI Engineering', 'Design Systems', 'Accessibility'],
    'Project-based, with short video primers',
    '30-45 min',
    '{"pace": "Steady (3-5 sessions / week)", "format": ["Interactive courses", "Hands-on projects", "Short assessments"], "difficulty": "Push me slightly beyond current level"}',
    '{"roadmapUpdates": true, "weeklyDigest": true, "assessmentReminders": true, "productNews": false}',
    'sk_react',
    '2026-05-12T00:00:00Z'
) ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 12. LEARNER SKILLS
-- Source: skillsData.js skills[] — proficiency and status per learner u_1001
-- last_assessed_at set for skills with completed assessments.
-- =============================================================================
INSERT INTO learner_skills (learner_id, skill_id, proficiency_score, status, last_assessed_at) VALUES
    ('u_1001', 'sk_html',           92, 'completed',    '2026-06-02T00:00:00Z'),
    ('u_1001', 'sk_css',            85, 'completed',    '2026-06-21T00:00:00Z'),
    ('u_1001', 'sk_js',             80, 'completed',    '2026-08-22T14:20:00Z'),  -- JS assessment scored 88%
    ('u_1001', 'sk_react',          28, 'current',      '2026-08-22T14:20:00Z'),  -- React Basics Check-in taken
    ('u_1001', 'sk_state',          10, 'adapted',      NULL),
    ('u_1001', 'sk_ts',             15, 'recommended',  NULL),
    ('u_1001', 'sk_testing',         0, 'locked',       NULL),
    ('u_1001', 'sk_a11y',           20, 'locked',       NULL),
    ('u_1001', 'sk_perf',            5, 'locked',       NULL),
    ('u_1001', 'sk_design_systems', 12, 'locked',       NULL)
ON CONFLICT (learner_id, skill_id) DO NOTHING;


-- =============================================================================
-- 13. LEARNING HISTORY
-- Source: userData.js currentUser.learningHistory[] (completed items)
--       + coursesData.js resources[] with progress > 0 (in-progress / completed)
--
-- lh_1 to lh_4: from userData.js learningHistory (completed, pre-catalog items)
-- lh_res_*: from coursesData.js per-learner progress tracking
-- =============================================================================
INSERT INTO learning_history (id, learner_id, resource_id, title, type, status, progress_pct, completed_at) VALUES
    -- From userData.js learningHistory[] — completed before current resource catalog
    ('lh_1', 'u_1001', NULL, 'HTML & Semantic Markup',    'course',   'completed', 100, '2026-06-02T00:00:00Z'),
    ('lh_2', 'u_1001', NULL, 'CSS Layout Systems',        'course',   'completed', 100, '2026-06-21T00:00:00Z'),
    ('lh_3', 'u_1001', NULL, 'JavaScript Fundamentals',   'course',   'completed', 100, '2026-07-18T00:00:00Z'),
    ('lh_4', 'u_1001', NULL, 'Personal Portfolio Site',   'project',  'completed', 100, '2026-07-25T18:40:00Z'),

    -- From coursesData.js resources with progress > 0 (current catalog items)
    -- res_1: React Fundamentals — in-progress 22%
    ('lh_res_1', 'u_1001', 'res_1', 'React Fundamentals',          'course',        'in-progress', 22,  NULL),
    -- res_3: Thinking in React — completed 100%
    ('lh_res_3', 'u_1001', 'res_3', 'Thinking in React (react.dev)', 'documentation', 'completed',   100, '2026-08-20T00:00:00Z'),
    -- res_4: CSS Grid in 15 Minutes — completed 100%
    ('lh_res_4', 'u_1001', 'res_4', 'CSS Grid in 15 Minutes',      'video',         'completed',   100, '2026-06-25T00:00:00Z'),
    -- res_8: Component Design Practice Set — in-progress 60%
    ('lh_res_8', 'u_1001', 'res_8', 'Component Design Practice Set', 'practice',    'in-progress', 60,  NULL)
ON CONFLICT (id) DO NOTHING;


-- =============================================================================
-- 14. LEARNER ROADMAP NODES
-- Source: roadmapData.js roadmapNodes[].status per learner u_1001
-- adapted_at set for nodes with status='adapted' (rm_state was AI-inserted).
-- =============================================================================
INSERT INTO learner_roadmap_nodes (learner_id, node_id, status, adapted_at) VALUES
    ('u_1001', 'rm_html',       'completed',    NULL),
    ('u_1001', 'rm_css',        'completed',    NULL),
    ('u_1001', 'rm_js',         'completed',    NULL),
    ('u_1001', 'rm_react',      'current',      NULL),
    ('u_1001', 'rm_state',      'adapted',      '2026-08-22T14:22:00Z'),  -- replanReason.triggeredAt
    ('u_1001', 'rm_project_1',  'recommended',  NULL),
    ('u_1001', 'rm_ts',         'recommended',  NULL),
    ('u_1001', 'rm_project_2',  'locked',       NULL),
    ('u_1001', 'rm_testing',    'locked',       NULL),
    ('u_1001', 'rm_assessment', 'locked',       NULL)
ON CONFLICT (learner_id, node_id) DO NOTHING;


-- =============================================================================
-- 15. ACTIVITY LOG
-- Source: userData.js recentActivity[] array
-- =============================================================================
INSERT INTO activity_log (learner_id, type, label, meta, reference_id, occurred_at) VALUES
    (
        'u_1001', 'assessment',
        'Completed "JavaScript Fundamentals" assessment',
        'Scored 88%',
        'as_react_basics',
        '2026-08-22T14:20:00Z'
    ),
    (
        'u_1001', 'roadmap',
        'Roadmap adapted after assessment results',
        'State Management added',
        'rm_state',
        '2026-08-22T14:22:00Z'
    ),
    (
        'u_1001', 'course',
        'Started "React Fundamentals"',
        '2 of 9 lessons complete',
        'res_1',
        '2026-08-23T09:05:00Z'
    ),
    (
        'u_1001', 'project',
        'Submitted "Portfolio Site" project',
        'Reviewed · Passed',
        'lh_4',
        '2026-07-25T18:40:00Z'
    );


-- =============================================================================
-- 16. ROADMAP REPLANS
-- Source: roadmapData.js replanReason + previousRoadmapPath + updatedRoadmapPath
-- =============================================================================
INSERT INTO roadmap_replans (
    learner_id,
    triggered_by_assessment_id,
    headline,
    reason,
    changes,
    previous_path,
    updated_path,
    triggered_at
) VALUES (
    'u_1001',
    'as_react_basics',
    'Your learning path has been updated',
    'Your assessment showed strong React fundamentals, but identified a gap in state management.',
    '[
        {"type": "added", "label": "React State Management", "detail": "New skill inserted right after React Fundamentals"},
        {"type": "added", "label": "Mini Project — Task Board", "detail": "Added to reinforce state management in practice"},
        {"type": "moved", "label": "TypeScript", "detail": "Pushed later to make room for the state-management gap"}
    ]',
    ARRAY['rm_react', 'rm_ts', 'rm_testing'],
    ARRAY['rm_react', 'rm_state', 'rm_project_1', 'rm_ts', 'rm_testing'],
    '2026-08-22T14:22:00Z'
) ON CONFLICT DO NOTHING;


-- =============================================================================
-- 17. RECOMMENDATIONS
-- Source: coursesData.js resources[].recommended = true for learner u_1001
-- score values are placeholder rankings (engine will recompute in Phase 2).
-- reasoning comes directly from resources[].whyRecommended in the mock.
-- =============================================================================
INSERT INTO recommendations (learner_id, resource_id, score, reasoning, is_active, generated_at) VALUES
    (
        'u_1001', 'res_1', 0.95,
        'Directly continues from your completed JavaScript course and is required for your target role.',
        TRUE, '2026-08-22T14:22:00Z'
    ),
    (
        'u_1001', 'res_2', 0.88,
        'Added after your assessment revealed a state-management gap.',
        TRUE, '2026-08-22T14:22:00Z'
    ),
    (
        'u_1001', 'res_5', 0.80,
        'Applies state management immediately after you learn it.',
        TRUE, '2026-08-22T14:22:00Z'
    ),
    (
        'u_1001', 'res_8', 0.75,
        'Reinforces concepts from React Fundamentals as you go.',
        TRUE, '2026-08-22T14:22:00Z'
    )
ON CONFLICT DO NOTHING;
