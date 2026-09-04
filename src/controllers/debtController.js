import { calculateGroupDebts } from '../utils/calculateDebts.js';
import { GroupMember } from '../models/index.js';

export const getGroupDebts = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const membership = await GroupMember.findOne({ where: { groupId, userId: req.userId } });
    if (!membership) return res.status(403).json({ message: 'Нет доступа' });
    const debts = await calculateGroupDebts(groupId);
    res.json(debts);
  } catch (err) { next(err); }
};

export const getMyDebts = async (req, res, next) => {
  try {
    const userId = req.userId;
    const memberships = await GroupMember.findAll({ where: { userId }, attributes: ['groupId'] });
    const groupIds = memberships.map(m => m.groupId);
    let allDebts = [];
    for (const groupId of groupIds) {
      const debts = await calculateGroupDebts(groupId);
      const myDebts = debts.filter(d => d.fromUserId === userId || d.toUserId === userId);
      allDebts = allDebts.concat(myDebts.map(d => ({ ...d, groupId })));
    }
    res.json(allDebts);
  } catch (err) { next(err); }
};

export const payDebt = async (req, res, next) => {
  res.status(501).json({ message: 'Функция в разработке' });
};