// worker/src/ralph-runner.ts
import { spawn } from 'child_process';
import { EventEmitter } from 'events';
import * as fs from 'fs/promises';
import * as path from 'path';
import { Redis } from 'ioredis';

interface RunConfig {
    projectId: string;
    userId: string;
    projectDir: string;
    maxIterations: number;
    model: 'sonnet' | 'opus';
    timeout: number;
}

interface IterationResult {
    iteration: number;
    agentId: string;
    success: boolean;
    duration: number;
    verification: Record<string, string>;
    logs: string[];
}

export class RalphRunner extends EventEmitter {
    private redis: Redis;
    private config: RunConfig;
    private isRunning: boolean = false;
    private currentIteration: number = 0;
    private process: ReturnType<typeof spawn> | null = null;

    constructor(redis: Redis, config: RunConfig) {
        super();
        this.redis = redis;
        this.config = config;
    }

    async start(): Promise<void> {
        if (this.isRunning) {
            throw new Error('Runner is already active');
        }

        this.isRunning = true;
        this.currentIteration = 0;

        // Publiziere Start-Event
        await this.publishEvent('run:started', {
            projectId: this.config.projectId,
            timestamp: new Date().toISOString(),
        });

        try {
            await this.runLoop();
        } catch (error) {
            await this.publishEvent('run:error', {
                error: error instanceof Error ? error.message : 'Unknown error',
            });
        } finally {
            this.isRunning = false;
            await this.publishEvent('run:completed', {
                totalIterations: this.currentIteration,
            });
        }
    }

    async stop(): Promise<void> {
        this.isRunning = false;
        if (this.process) {
            this.process.kill('SIGTERM');
        }
    }

    private async runLoop(): Promise<void> {
        while (this.isRunning && this.currentIteration < this.config.maxIterations) {
            this.currentIteration++;

            const result = await this.runIteration();

            await this.publishEvent('iteration:completed', { ...result });

            // Check for completion
            const completePath = path.join(this.config.projectDir, '.ralph', 'COMPLETE');
            if (await this.fileExists(completePath)) {
                await this.publishEvent('task:completed', {
                    iterations: this.currentIteration,
                });
                break;
            }

            // Kurze Pause
            await this.sleep(2000);
        }
    }

    private async runIteration(): Promise<IterationResult> {
        const startTime = Date.now();
        const logs: string[] = [];

        return new Promise((resolve, reject) => {
            this.process = spawn('bash', [
                path.join(__dirname, 'ralph-single-iteration.sh'),
                this.config.projectDir,
                this.currentIteration.toString(),
            ], {
                env: {
                    ...process.env,
                    MODEL: this.config.model,
                    ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY,
                },
                cwd: this.config.projectDir,
            });

            this.process.stdout?.on('data', (data) => {
                const line = data.toString();
                logs.push(line);
                this.emit('log', { iteration: this.currentIteration, line });
            });

            this.process.stderr?.on('data', (data) => {
                logs.push(`[stderr] ${data.toString()}`);
            });

            this.process.on('close', async (code) => {
                const duration = Date.now() - startTime;
                const verification = await this.readVerificationResult();

                resolve({
                    iteration: this.currentIteration,
                    agentId: await this.getCurrentAgent(),
                    success: code === 0,
                    duration,
                    verification,
                    logs,
                });
            });

            this.process.on('error', reject);
        });
    }

    private async publishEvent(event: string, data: Record<string, unknown>): Promise<void> {
        const channel = `project:${this.config.projectId}:events`;
        await this.redis.publish(channel, JSON.stringify({
            event,
            data,
            timestamp: new Date().toISOString(),
        }));
    }

    private async fileExists(filePath: string): Promise<boolean> {
        try {
            await fs.access(filePath);
            return true;
        } catch {
            return false;
        }
    }

    private async getCurrentAgent(): Promise<string> {
        try {
            const genealogy = JSON.parse(
                await fs.readFile(
                    path.join(this.config.projectDir, '.dgm', 'genealogy.json'),
                    'utf-8'
                )
            );
            return genealogy.agents[genealogy.agents.length - 1] || 'agent-001';
        } catch {
            return 'agent-001';
        }
    }

    private async readVerificationResult(): Promise<Record<string, string>> {
        try {
            const resultPath = path.join(this.config.projectDir, '.ralph', 'last-verification.json');
            return JSON.parse(await fs.readFile(resultPath, 'utf-8'));
        } catch {
            return {};
        }
    }

    private sleep(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
