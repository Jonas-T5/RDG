// components/RunDashboard.tsx
import React, { useEffect, useState, useRef } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface Run {
    id: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
    currentIteration: number;
    totalIterations: number;
    currentAgent: string;
}

interface IterationEvent {
    iteration: number;
    agentId: string;
    success: boolean;
    duration: number;
    logs: string[];
}

interface MetricCardProps {
    label: string;
    value: string | number;
    max?: number;
}

function MetricCard({ label, value, max }: MetricCardProps) {
    return (
        <div className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value">
                {value}
                {max !== undefined && <span className="metric-max">/ {max}</span>}
            </div>
        </div>
    );
}

function calculateSuccessRate(iterations: IterationEvent[]): string {
    if (iterations.length === 0) return '0%';
    const successCount = iterations.filter(i => i.success).length;
    return `${Math.round((successCount / iterations.length) * 100)}%`;
}

interface IterationTimelineProps {
    iterations: IterationEvent[];
}

function IterationTimeline({ iterations }: IterationTimelineProps) {
    return (
        <div className="iteration-timeline">
            <h2>Iterations</h2>
            <div className="timeline">
                {iterations.map((iter) => (
                    <div
                        key={iter.iteration}
                        className={`timeline-item ${iter.success ? 'success' : 'failure'}`}
                    >
                        <span className="iteration-number">#{iter.iteration}</span>
                        <span className="agent-id">{iter.agentId}</span>
                        <span className="duration">{(iter.duration / 1000).toFixed(1)}s</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

interface LogViewerProps {
    logs: string[];
}

function LogViewer({ logs }: LogViewerProps) {
    const logRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (logRef.current) {
            logRef.current.scrollTop = logRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="log-viewer" ref={logRef}>
            <h2>Live Logs</h2>
            <pre className="log-content">
                {logs.map((log, i) => (
                    <div key={i} className="log-line">{log}</div>
                ))}
            </pre>
        </div>
    );
}

interface RunDashboardProps {
    runId: string;
}

export function RunDashboard({ runId }: RunDashboardProps) {
    const [run, setRun] = useState<Run | null>(null);
    const [iterations, setIterations] = useState<IterationEvent[]>([]);
    const [logs, setLogs] = useState<string[]>([]);

    const { lastMessage } = useWebSocket(`/ws/runs/${runId}`);

    useEffect(() => {
        // Fetch initial run state
        fetch(`/api/runs/${runId}`)
            .then(res => res.json())
            .then(data => {
                setRun({
                    id: data.id,
                    status: data.status,
                    currentIteration: data.current_iteration,
                    totalIterations: data.total_iterations,
                    currentAgent: data.current_agent,
                });
            });
    }, [runId]);

    useEffect(() => {
        if (lastMessage) {
            try {
                const event = JSON.parse(lastMessage.data);

                switch (event.event) {
                    case 'iteration:completed':
                        setIterations(prev => [...prev, event.data]);
                        setRun(prev => prev ? {
                            ...prev,
                            currentIteration: event.data.iteration,
                            currentAgent: event.data.agentId,
                        } : null);
                        break;

                    case 'run:completed':
                        setRun(prev => prev ? { ...prev, status: 'completed' } : null);
                        break;

                    case 'run:error':
                        setRun(prev => prev ? { ...prev, status: 'failed' } : null);
                        break;

                    case 'log':
                        setLogs(prev => [...prev, event.data.line]);
                        break;
                }
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        }
    }, [lastMessage]);

    const handleStop = async () => {
        await fetch(`/api/runs/${runId}/stop`, { method: 'POST' });
        setRun(prev => prev ? { ...prev, status: 'stopped' } : null);
    };

    if (!run) {
        return <div className="loading">Loading...</div>;
    }

    return (
        <div className="run-dashboard">
            <header className="run-header">
                <h1>Run: {runId.slice(0, 8)}...</h1>
                <div className={`status-badge status-${run.status}`}>
                    {run.status}
                </div>
                {run.status === 'running' && (
                    <button onClick={handleStop} className="stop-button">
                        Stop Run
                    </button>
                )}
            </header>

            <div className="metrics-grid">
                <MetricCard
                    label="Current Iteration"
                    value={run.currentIteration}
                    max={run.totalIterations}
                />
                <MetricCard
                    label="Current Agent"
                    value={run.currentAgent}
                />
                <MetricCard
                    label="Success Rate"
                    value={calculateSuccessRate(iterations)}
                />
            </div>

            <div className="panels">
                <IterationTimeline iterations={iterations} />
                <LogViewer logs={logs} />
            </div>
        </div>
    );
}

export default RunDashboard;
