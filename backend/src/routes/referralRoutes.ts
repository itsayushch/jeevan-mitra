import { Router } from 'express';
import { ReferralController } from '../controllers/referralController.js';

const router = Router();
const controller = new ReferralController();

router.get('/', controller.listReferrals);
router.get('/:id', controller.getReferralById);
router.patch('/:id', controller.updateReferral);
router.post('/outcomes', controller.recordOutcome);
router.get('/progress/:beneficiaryId', controller.getBeneficiaryProgressTracker);

export default router;
