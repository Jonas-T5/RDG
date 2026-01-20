// components/AgentGenealogy.tsx
import React, { useMemo } from 'react';
import * as d3 from 'd3';

interface Agent {
    id: string;
    parentId: string | null;
    generation: number;
    mutationType: string;
    benchmarkResults: {
        testPassRate?: number;
    };
}

interface GenealogyData {
    agents: string[];
    edges: Array<{ from: string; to: string }>;
}

interface TreeNode {
    id: string;
    parentId: string | null;
    generation: number;
    mutationType: string;
    benchmarkResults: {
        testPassRate?: number;
    };
    children?: TreeNode[];
}

function getNodeColor(agent: Agent): string {
    const passRate = agent.benchmarkResults?.testPassRate || 0;
    if (passRate >= 0.9) return '#22c55e';  // Green
    if (passRate >= 0.7) return '#eab308';  // Yellow
    if (passRate >= 0.5) return '#f97316';  // Orange
    return '#ef4444';  // Red
}

interface AgentGenealogyProps {
    genealogy: GenealogyData;
    agents: Agent[];
}

export function AgentGenealogy({ genealogy, agents }: AgentGenealogyProps) {
    const treeData = useMemo(() => {
        // Konvertiere zu Hierarchie für D3
        const agentMap = new Map(agents.map(a => [a.id, a]));

        const root = agents.find(a => a.parentId === null);
        if (!root) return null;

        function buildTree(agentId: string): TreeNode {
            const agent = agentMap.get(agentId);
            if (!agent) {
                return {
                    id: agentId,
                    parentId: null,
                    generation: 0,
                    mutationType: 'unknown',
                    benchmarkResults: {},
                };
            }

            const children = genealogy.edges
                .filter(e => e.from === agentId)
                .map(e => buildTree(e.to));

            return {
                ...agent,
                children: children.length > 0 ? children : undefined,
            };
        }

        return d3.hierarchy(buildTree(root.id));
    }, [genealogy, agents]);

    if (!treeData) {
        return (
            <div className="genealogy-empty">
                <p>No agents yet</p>
            </div>
        );
    }

    const width = 800;
    const height = 600;
    const treeLayout = d3.tree<TreeNode>().size([width - 100, height - 100]);
    const tree = treeLayout(treeData);

    return (
        <div className="genealogy-container">
            <h2>Agent Genealogy Tree</h2>
            <svg width={width} height={height} className="genealogy-tree">
                <g transform="translate(50, 50)">
                    {/* Edges */}
                    {tree.links().map((link, i) => (
                        <path
                            key={i}
                            d={d3.linkVertical<d3.HierarchyLink<TreeNode>, d3.HierarchyPointNode<TreeNode>>()
                                .x((d) => d.x)
                                .y((d) => d.y)(link as any) || ''}
                            fill="none"
                            stroke="#666"
                            strokeWidth={2}
                        />
                    ))}

                    {/* Nodes */}
                    {tree.descendants().map((node, i) => (
                        <g key={i} transform={`translate(${node.x}, ${node.y})`}>
                            <circle
                                r={20}
                                fill={getNodeColor(node.data as Agent)}
                                stroke="#333"
                                strokeWidth={2}
                            />
                            <text
                                dy={4}
                                textAnchor="middle"
                                fontSize={10}
                                fill="white"
                            >
                                {node.data.generation}
                            </text>
                            <text
                                dy={35}
                                textAnchor="middle"
                                fontSize={9}
                            >
                                {node.data.id}
                            </text>
                            <title>
                                {`${node.data.id}\nGeneration: ${node.data.generation}\nType: ${node.data.mutationType}`}
                            </title>
                        </g>
                    ))}
                </g>
            </svg>

            <div className="genealogy-legend">
                <h3>Legend (Test Pass Rate)</h3>
                <div className="legend-items">
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#22c55e' }}></span>
                        <span>90%+</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#eab308' }}></span>
                        <span>70-89%</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#f97316' }}></span>
                        <span>50-69%</span>
                    </div>
                    <div className="legend-item">
                        <span className="legend-color" style={{ backgroundColor: '#ef4444' }}></span>
                        <span>&lt;50%</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AgentGenealogy;
