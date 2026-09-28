import { Router } from 'express';
import { PlanningController } from '../controllers/planningController.js';

const router = Router();
const controller = new PlanningController();

router.get('/supply-gap-matrix', controller.getDemandSupplyMatrix);
router.post('/generate-brief', controller.generateBrief);
router.get('/briefs', controller.listBriefs);
router.get('/briefs/:id', controller.getBriefById);
router.post('/briefs/:id/sign-off', controller.signOff);
router.get('/export', controller.exportPlan);

export default router;
