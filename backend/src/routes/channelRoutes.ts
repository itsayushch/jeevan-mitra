import { Router } from 'express';
import { ChannelController } from '../controllers/channelController.js';

const router = Router();
const controller = new ChannelController();

router.post('/whatsapp/simulate', controller.handleWhatsAppVoice);
router.post('/ivr/simulate', controller.handleIvrCall);

export default router;
