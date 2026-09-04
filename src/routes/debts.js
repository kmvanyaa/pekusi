import { Router } from 'express';
import { getGroupDebts, getMyDebts, payDebt } from '../controllers/debtController.js';

const router = Router();

router.get('/group/:groupId', getGroupDebts);
router.get('/my', getMyDebts);
router.post('/:debtId/pay', payDebt);

export default router;