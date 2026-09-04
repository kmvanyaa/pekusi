import { Router } from 'express';
import { register, login, loginByTelegram, linkTelegram } from '../controllers/authController.js';
import { validate } from '../middlewares/validate.js';
import { registerSchema, loginSchema, linkTelegramSchema } from '../schemas/authSchema.js';
import { auth } from '../middlewares/auth.js';

const router = Router();

router.post('/register', validate(registerSchema), register);
router.post('/login', validate(loginSchema), login);
router.post('/telegram', loginByTelegram);
router.post('/link-telegram', auth, validate(linkTelegramSchema), linkTelegram);

export default router;