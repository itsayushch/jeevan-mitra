import { Router } from 'express';
import { HealthController } from '../controllers/healthController.js';
import beneficiaryRoutes from './beneficiaryRoutes.js';
import consentRoutes from './consentRoutes.js';
import interviewRoutes from './interviewRoutes.js';
import recommendationRoutes from './recommendationRoutes.js';
import workerRoutes from './workerRoutes.js';
import referralRoutes from './referralRoutes.js';
import planningRoutes from './planningRoutes.js';
import monitoringRoutes from './monitoringRoutes.js';
import channelRoutes from './channelRoutes.js';
import auditRoutes from './auditRoutes.js';
import catalogueRoutes from './catalogueRoutes.js';
import chatRoutes from './chatRoutes.js';
import { authenticate } from '../middleware/authMiddleware.js';

const router = Router();
const healthController = new HealthController();

router.get('/health', healthController.check);

// Channels/webhooks should be public (or have their own specific auth)
router.use('/channels', channelRoutes);

// Apply authentication to all other routes
router.use(authenticate);

router.use('/beneficiaries', beneficiaryRoutes);
router.use('/consents', consentRoutes);
router.use('/interview', interviewRoutes);
router.use('/recommendations', recommendationRoutes);
router.use('/worker', workerRoutes);
router.use('/referrals', referralRoutes);
router.use('/planning', planningRoutes);
router.use('/monitoring', monitoringRoutes);
router.use('/audit-events', auditRoutes);
router.use('/catalogue', catalogueRoutes);
router.use('/chat', chatRoutes);

export default router;
