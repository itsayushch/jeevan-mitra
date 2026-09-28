import { Router } from 'express';
import { BeneficiaryController } from '../controllers/beneficiaryController.js';

const router = Router();
const controller = new BeneficiaryController();

router.post('/', controller.create);
router.get('/', controller.list);
router.get('/:id', controller.getById);
router.patch('/:id', controller.update);

export default router;
