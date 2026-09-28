import { Router } from 'express';
import { ConsentController } from '../controllers/consentController.js';

const router = Router();
const controller = new ConsentController();

router.post('/', controller.record);
router.get('/beneficiary/:beneficiaryId', controller.getByBeneficiary);

export default router;
