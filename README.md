Markdown
<div align="center">

# 🧭 Bugged Brains — Career Pathfinder
### *AI-Powered Personalized Learning Path Recommender*

**A smarter way to guide learners from where they are to where they want to be.**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Vercel-black?style=for-the-badge&logo=vercel)](https://careerpathfinder-git-main-sanchits-projects-3e58d5f5.vercel.app/)
[![GitHub Repo](https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github)](https://github.com/ShashiBhushanSharma-debug/Bugged-Brains---Career-Pathfinder)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge)](LICENSE)

[🌐 View Live Site](https://careerpathfinder-git-main-sanchits-projects-3e58d5f5.vercel.app/) • [🐛 Report Bug](https://github.com/ShashiBhushanSharma-debug/Bugged-Brains---Career-Pathfinder/issues) • [✨ Request Feature](https://github.com/ShashiBhushanSharma-debug/Bugged-Brains---Career-Pathfinder/issues)

</div>

---

## 📌 Table of Contents

- [Overview](#-overview)
- [The Problem We Solve](#-the-problem-we-solve)
- [The Solution](#-the-solution)
- [Core AI Engines & Architecture](#-core-ai-engines--architecture)
- [Dashboard Experience & UI Modules](#-dashboard-experience--ui-modules)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Running Locally](#running-locally)
- [Folder Structure](#-folder-structure)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [Team & Acknowledgments](#-team--acknowledgments)
- [License](#-license)

---

## 🚀 Overview

**Career Pathfinder** is an AI-powered intelligent career assistant designed to eliminate the trial-and-error approach to online education. Instead of offering generic, static course catalogs, the platform dynamically analyzes a learner's current baseline, pinpoints exact skill deficiencies against their target career role, and outputs a personalized, adaptive milestone roadmap.

---

## 🛑 The Problem We Solve

Traditional online learning fails because of three fundamental friction points:

1. **Overwhelming Choice:** Millions of tutorials and courses exist, yet students struggle to identify the correct prerequisite sequence.
2. **Lack of Personalization:** Every learner starts with unique prior experience, time availability, and target roles; one-size-fits-all curricula fail to adapt.
3. **No Clear, Structured Roadmap:** Learners lack an end-to-end milestone tracker showing direct progression from their current state to an industry-ready role.

---

## 💡 The Solution

An intelligent assistant designed around four core interactions:

- **Conversational Onboarding:** Learners express their goals and background naturally without getting lost in rigid forms.
- **AI Recommendation Engine:** Surfaces the exact course, project, or documentation snippet needed at that exact milestone.
- **Personalized & Adaptive Path:** Dynamically recalibrates prerequisites and milestones as the user makes progress or gives feedback.
- **Progress Tracking Hub:** Provides live readiness scoring, weekly pace analytics, and streak tracking to keep learners consistently motivated.

---

## 🧠 Core AI Engines & Architecture

Career Pathfinder operates on three interconnected intelligent engines:

+--------------------------+      +---------------------------+      +---------------------------+
|  Learner Profiling Engine| ---> |   Recommendation Engine   | ---> |  Path Generator & Adapter |
|  • Interests & Domain    |      |   • Skill Gap Analysis    |      |  • Milestone Generation   |
|  • Experience Level      |      |   • Curated Multi-Format  |      |  • Real-time Recalibration|
|  • Learning History      |      |   • Transparent Rationale |      |  • Feedback Loop          |
+--------------------------+      +---------------------------+      +---------------------------+


### 1. Learner Profiling Engine (Dynamic Profile)
Builds and maintains an evolving profile rather than a static intake form. It constantly recalculates four distinct vectors:
- **Interests:** Core technical topics and desired domains.
- **Experience Level:** Beginner, Intermediate, or Advanced baseline.
- **Learning History:** Completed modules, prior courses, and demonstrated skills.
- **Target Objectives:** Specific job positions (e.g., *Frontend Developer: Intermediate-Advanced*).

### 2. Recommendation Engine
- **Skill Gap Analysis:** Measures the exact delta between current competencies and industry expectations for the target role.
- **Multi-Format Curation:** Sequences optimal learning materials across practice tasks, video tutorials, articles, documentation, and mini-projects.
- **Transparent Reasoning:** Every recommendation is accompanied by an AI explanation detailing *why* that specific module was assigned.

### 3. Path Generator & Adaptive Learning
- Operates on a continuous loop: **`Generate Path`** $\rightarrow$ **`Monitor Progress`** $\rightarrow$ **`Collect Feedback`** $\rightarrow$ **`Adapt Recommendations`**.
- Automatically re-routes the syllabus if a learner breezes through basics or requires additional practice in complex topics.

---

## 🖥️ Dashboard Experience & UI Modules

The frontend interface translates complex AI planning into three focused user views:

| View | Purpose | Key Metrics & Components |
|---|---|---|
| **Career Readiness Overview** | High-level trajectory & standing | • Prominent Target Role header<br>• Career Readiness Gauge (%)<br>• Overall Milestone Progress (%)<br>• Daily Streak & Weekly Hours Goal |
| **Current Focus (Learning Hub)** | Daily actionable tasks | • Active learning item with rationale<br>• Multi-category filtering (*Video, Article, Practice, Docs, Project*)<br>• Estimated completion time & difficulty level |
| **Progress Tracking & Mastery** | Proof of growth & motivation | • Total Skills Mastered count<br>• Completed Projects count<br>• Assessments Taken count<br>• Weekly Learning Pace graph |

---

## 🛠️ Tech Stack

- **Frontend:** Next.js / React, Tailwind CSS, Lucide Icons, Radix UI
- **State Management & Routing:** Next.js App/Pages Router
- **Deployment & Hosting:** [Vercel](https://vercel.com/)
- **Version Control:** Git & GitHub

---

## ⚙️ Getting Started

Follow these steps to set up the project locally.

### Prerequisites

- [Node.js](https://nodejs.org/) (`v18.x` or higher)
- [npm](https://www.npmjs.com/) / [yarn](https://yarnpkg.com/) / [pnpm](https://pnpm.io/)
- [Git](https://git-scm.com/)

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/ShashiBhushanSharma-debug/Bugged-Brains---Career-Pathfinder.git](https://github.com/ShashiBhushanSharma-debug/Bugged-Brains---Career-Pathfinder.git)
   cd Bugged-Brains---Career-Pathfinder
Install dependencies:

Bash
npm install
# or
yarn install
# or
pnpm install
Configure Environment Variables:
Create a .env.local file in the root directory:

Code snippet
NEXT_PUBLIC_APP_URL=http://localhost:3000
Run the local development server:

Bash
npm run dev
# or
yarn dev
Open the app:
Open your browser and navigate to http://localhost:3000.

📂 Folder Structure
Plaintext
Bugged-Brains---Career-Pathfinder/
├── public/                 # Static assets, logos, and icons
├── src/
│   ├── components/         # Reusable UI components (Navbar, StatsCard, RoadmapView)
│   │   ├── dashboard/      # Readiness gauge, progress widgets
│   │   ├── learning-hub/   # Resource filters, module cards
│   │   └── common/         # Buttons, badges, layouts
│   ├── pages/ or app/      # Application routes (Overview, Roadmap, Skills, Learn)
│   ├── styles/             # Global styles and Tailwind configuration
│   ├── utils/              # Calculation helpers and analytics
│   └── data/               # Curated resource catalog, role requirement maps
├── .env.example            # Sample environment variables
├── package.json            # Project dependencies and build scripts
└── README.md               # Project documentation
🗺️ Roadmap
[x] Personalized dynamic onboarding & profile initialization

[x] Multi-format Learning Queue (Videos, Docs, Mini-Projects, Practice)

[x] Readiness score and weekly learning pace tracker

[ ] AI-assisted interactive resume review and skill gap extraction

[ ] Automated code assessments and sandbox integration

[ ] Peer community and mentorship matching

🤝 Contributing
Contributions make open-source a great place to build and innovate. Any improvements or fixes are welcome!

Fork the repository

Create a feature branch (git checkout -b feature/NewFeature)

Commit your changes (git commit -m 'Add NewFeature')

Push to the branch (git push origin feature/NewFeature)

Open a Pull Request

👥 Team — Bugged Brains
Shashi Bhushan Sharma — @ShashiBhushanSharma-debug

Sanchit & the Bugged Brains Team

📄 License
This project is licensed under the MIT License — see the LICENSE file for details.


---

### 📝 Is README ko use kaise karein:
1. Apne GitHub repo ke root folder mein `README.md` file banayein ya edit karein.
2. Upar diya gaya markdown content paste karein aur commit kar dein.
3. Agar dashboard ke screenshots add karne hain, toh repo mein ek `docs/` ya `public/` folder banakar image upload karein aur README mein `![Dashboard Preview](./public/dashboard.png)` tag lagakar dikha dein.

<ElicitationsGroup message="Next steps to complete your repo setup:">
  <Elicitation label="Generate MIT License content" query="Provide standard MIT license text with copyright holders for Bugged Brains Career Pathfinder."/>
  <Elicitation label="Create GitHub issue and PR templates" query="Create GitHub issue and pull request templates for Bugged-Brains---Career-Pathfinder."/>
  <Elicitation label="Generate project viva / interview Q&A" query="Generate 10 technical viva and interview questions with answers based on this project architecture."/>
</ElicitationsGroup>
