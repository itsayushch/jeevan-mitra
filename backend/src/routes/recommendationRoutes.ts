import { Router } from 'express';
import { RecommendationController } from '../controllers/recommendationController.js';

const router = Router();
const controller = new RecommendationController();

router.post('/match', controller.match);
router.get('/beneficiary/:beneficiaryId', controller.getByBeneficiary);
router.get('/:id/details', controller.getDetails);
router.get('/:id/opportunity', controller.getCentreDetails);
router.get('/compare/:id1/:id2', controller.compare);

export default router;
