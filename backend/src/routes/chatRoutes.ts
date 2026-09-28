import { Router } from 'express';
import { ChatController } from '../controllers/chatController.js';

const router = Router();
const chatController = new ChatController();

router.get('/', chatController.handleChat);
router.post('/', chatController.handleChat);

export default router;
