import { createApp } from './app.js';
import { env } from './config/env.js';
import { seedDatabase } from './database/seed.js';
import { closeDatabase } from './database/connection.js';
import { logger } from './utils/logger.js';

async function bootstrap() {
  logger.info('Starting JeevanMitra 2.0 Backend Core Service...');
  logger.info(`Operating Environment: ${env.NODE_ENV} | Pilot District: ${env.DEFAULT_DISTRICT}`);

  // Ensure DB schema and seeds are active
  seedDatabase();

  const app = createApp();

  const server = app.listen(env.PORT, env.HOST, () => {
    logger.info(`================================================================`);
    logger.info(`  JEEVAN-MITRA 2.0 BACKEND SERVICE IS OPERATIONAL`);
    logger.info(`  MoSJE PM-AJAY GIA Component (Problem Statement ID 26097)`);
    logger.info(`================================================================`);
    logger.info(`  Server URL:             http://${env.HOST}:${env.PORT}`);
    logger.info(`  Health Check:           http://${env.HOST}:${env.PORT}/api/health`);
    logger.info(`  Claim 1 Invariant:      Verified Match Protocol [ACTIVE]`);
    logger.info(`  Claim 2 Planning Loop:  Aggregated Supply-Gap Engine [ACTIVE]`);
    logger.info(`  Six AI Layers:          L1 Intake, L2 Extraction, L3 RAG Matcher,`);
    logger.info(`                          L4 Co-Pilot, L5 Narrative Brief, L6 Bias Drift`);
    logger.info(`================================================================`);
  });

  const handleShutdown = () => {
    logger.info('Gracefully shutting down JeevanMitra 2.0 backend...');
    server.close(() => {
      closeDatabase();
      logger.info('Database connection closed. Process terminated.');
      process.exit(0);
    });
  };

  process.on('SIGINT', handleShutdown);
  process.on('SIGTERM', handleShutdown);
}

bootstrap().catch((err) => {
  logger.error('Fatal error during backend initialization', { error: err.message, stack: err.stack });
  process.exit(1);
});
