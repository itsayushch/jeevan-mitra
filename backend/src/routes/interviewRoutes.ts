import { Router } from 'express';
import { InterviewController } from '../controllers/interviewController.js';

const router = Router();
const controller = new InterviewController();

router.post('/start', controller.start);
router.post('/turn', controller.processTurn);
router.get('/extract/:sessionId', controller.extractProfile);
router.post('/confirm', controller.confirmProfile);
router.get('/session/:id', controller.getSession);

export default router;
