import { Router } from 'express';
import { MonitoringController } from '../controllers/monitoringController.js';

const router = Router();
const controller = new MonitoringController();

router.post('/audit-drift', controller.auditDrift);
router.get('/advisories', controller.getAdvisories);
router.patch('/advisories/:id', controller.updateAdvisory);

export default router;
