// app/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { RunDashboard } from '../components/RunDashboard';
import { AgentGenealogy } from '../components/AgentGenealogy';

interface Project {
    id: string;
    name: string;
    description: string;
    created_at: string;
}

interface Run {
    id: string;
    project_id: string;
    status: string;
    current_iteration: number;
    total_iterations: number;
}

export default function Home() {
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProject, setSelectedProject] = useState<string | null>(null);
    const [activeRun, setActiveRun] = useState<Run | null>(null);
    const [genealogy, setGenealogy] = useState<any>(null);
    const [agents, setAgents] = useState<any[]>([]);
    const [view, setView] = useState<'dashboard' | 'genealogy'>('dashboard');

    useEffect(() => {
        // Fetch projects
        fetch('/api/projects')
            .then(res => res.json())
            .then(setProjects)
            .catch(console.error);
    }, []);

    useEffect(() => {
        if (selectedProject) {
            // Fetch genealogy
            fetch(`/api/projects/${selectedProject}/genealogy`)
                .then(res => res.json())
                .then(setGenealogy)
                .catch(console.error);

            // Fetch agents
            fetch(`/api/projects/${selectedProject}/agents`)
                .then(res => res.json())
                .then(setAgents)
                .catch(console.error);
        }
    }, [selectedProject]);

    const handleStartRun = async () => {
        if (!selectedProject) return;

        const response = await fetch(`/api/projects/${selectedProject}/runs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                max_iterations: 100,
                model: 'sonnet',
                timeout_per_iteration: 600,
            }),
        });

        const run = await response.json();
        setActiveRun(run);
    };

    return (
        <main className="container">
            <header className="header">
                <h1>Darwin Gödel Machine</h1>
                <p>Self-improving AI Agent System with Ralph Loop</p>
            </header>

            <nav className="nav">
                <button
                    className={view === 'dashboard' ? 'active' : ''}
                    onClick={() => setView('dashboard')}
                >
                    Dashboard
                </button>
                <button
                    className={view === 'genealogy' ? 'active' : ''}
                    onClick={() => setView('genealogy')}
                >
                    Agent Genealogy
                </button>
            </nav>

            <section className="project-selector">
                <h2>Projects</h2>
                <div className="project-list">
                    {projects.map(project => (
                        <div
                            key={project.id}
                            className={`project-card ${selectedProject === project.id ? 'selected' : ''}`}
                            onClick={() => setSelectedProject(project.id)}
                        >
                            <h3>{project.name}</h3>
                            <p>{project.description}</p>
                        </div>
                    ))}
                </div>

                {selectedProject && (
                    <div className="project-actions">
                        <button onClick={handleStartRun} className="start-button">
                            Start New Run
                        </button>
                    </div>
                )}
            </section>

            {view === 'dashboard' && activeRun && (
                <RunDashboard runId={activeRun.id} />
            )}

            {view === 'genealogy' && genealogy && (
                <AgentGenealogy genealogy={genealogy} agents={agents} />
            )}

            <style jsx>{`
                .container {
                    max-width: 1400px;
                    margin: 0 auto;
                    padding: 2rem;
                }

                .header {
                    text-align: center;
                    margin-bottom: 2rem;
                }

                .header h1 {
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                }

                .header p {
                    color: #94a3b8;
                }

                .nav {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 2rem;
                    border-bottom: 1px solid #334155;
                    padding-bottom: 1rem;
                }

                .nav button {
                    padding: 0.5rem 1rem;
                    background: none;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    font-size: 1rem;
                }

                .nav button.active {
                    color: #3b82f6;
                    border-bottom: 2px solid #3b82f6;
                }

                .project-selector {
                    margin-bottom: 2rem;
                }

                .project-selector h2 {
                    font-size: 1.25rem;
                    margin-bottom: 1rem;
                }

                .project-list {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 1rem;
                    margin-bottom: 1rem;
                }

                .project-card {
                    background: #1e293b;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    border: 1px solid #334155;
                    cursor: pointer;
                    transition: border-color 0.2s;
                }

                .project-card:hover {
                    border-color: #3b82f6;
                }

                .project-card.selected {
                    border-color: #3b82f6;
                    background: rgba(59, 130, 246, 0.1);
                }

                .project-card h3 {
                    font-size: 1rem;
                    margin-bottom: 0.5rem;
                }

                .project-card p {
                    font-size: 0.875rem;
                    color: #94a3b8;
                }

                .project-actions {
                    margin-top: 1rem;
                }

                .start-button {
                    padding: 0.75rem 1.5rem;
                    background: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 0.375rem;
                    cursor: pointer;
                    font-weight: 500;
                }

                .start-button:hover {
                    background: #2563eb;
                }
            `}</style>
        </main>
    );
}
