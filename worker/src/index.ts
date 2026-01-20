// worker/src/index.ts
import { Redis } from 'ioredis';
import { RalphRunner } from './ralph-runner';

const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

interface JobData {
    run_id: string;
    project_id: string;
    user_id: string;
    project_dir: string;
    config: {
        max_iterations: number;
        model: 'sonnet' | 'opus';
        timeout_per_iteration: number;
    };
}

async function processJob(jobData: JobData): Promise<void> {
    console.log(`[Worker] Processing job: ${jobData.run_id}`);

    const runner = new RalphRunner(redis, {
        projectId: jobData.project_id,
        userId: jobData.user_id,
        projectDir: jobData.project_dir,
        maxIterations: jobData.config.max_iterations,
        model: jobData.config.model,
        timeout: jobData.config.timeout_per_iteration,
    });

    runner.on('log', (logData) => {
        console.log(`[Iteration ${logData.iteration}] ${logData.line}`);
    });

    await runner.start();
}

async function main(): Promise<void> {
    console.log('[Worker] Darwin Gödel Machine Worker started');
    console.log('[Worker] Waiting for jobs...');

    // Simple job queue processing using Redis lists
    while (true) {
        try {
            const result = await redis.brpop('dgm:jobs', 0);
            if (result) {
                const [, jobJson] = result;
                const jobData: JobData = JSON.parse(jobJson);
                await processJob(jobData);
            }
        } catch (error) {
            console.error('[Worker] Error processing job:', error);
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    }
}

main().catch(console.error);
