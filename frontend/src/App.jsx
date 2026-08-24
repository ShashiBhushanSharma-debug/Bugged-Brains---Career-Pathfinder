import { Routes, Route } from 'react-router-dom';
import AppLayout from './components/AppLayout';

import Landing from './pages/Landing';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import SkillAnalysis from './pages/SkillAnalysis';
import RoadmapPage from './pages/RoadmapPage';
import LearningHub from './pages/LearningHub';
import Resources from './pages/Resources';
import Assessments from './pages/Assessments';
import Assessment from './pages/Assessment';
import AdaptiveReplanning from './pages/AdaptiveReplanning';
import Progress from './pages/Progress';
import Profile from './pages/Profile';
import Settings from './pages/Settings';

export default function App() {
  return (
    <Routes>
      {/* Standalone routes — no app shell */}
      <Route path="/" element={<Landing />} />
      <Route path="/onboarding" element={<Onboarding />} />

      {/* Authenticated app shell */}
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analysis" element={<SkillAnalysis />} />
        <Route path="/roadmap" element={<RoadmapPage />} />
        <Route path="/adaptive" element={<AdaptiveReplanning />} />
        <Route path="/learn" element={<LearningHub />} />
        <Route path="/resources" element={<Resources />} />
        <Route path="/assessments" element={<Assessments />} />
        <Route path="/assessment/:id" element={<Assessment />} />
        <Route path="/progress" element={<Progress />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<Landing />} />
    </Routes>
  );
}