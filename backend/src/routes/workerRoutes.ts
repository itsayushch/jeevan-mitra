import { Router } from 'express';
import { WorkerController } from '../controllers/workerController.js';

const router = Router();
const controller = new WorkerController();

router.get('/cases', controller.getCases);
router.get('/cases/:id', controller.getCaseDetail);
router.patch('/cases/:id/profile', controller.correctProfile);
router.post('/cases/:id/verify-batch', controller.verifyBatch);
router.post('/cases/:id/referral', controller.approveReferral);

export default router;
