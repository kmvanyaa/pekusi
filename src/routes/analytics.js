import { Router } from 'express';
import { getMonthlySummary, getDailyAnalytics, getBudgetPrediction } from '../controllers/analyticsController.js';

const router = Router();

router.get('/group/:groupId/summary', getMonthlySummary);
router.get('/group/:groupId/daily', getDailyAnalytics);
router.get('/group/:groupId/prediction', getBudgetPrediction);

export default router;