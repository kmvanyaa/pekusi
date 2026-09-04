import { Op } from 'sequelize';
import { Expense, ExpenseSplit, GroupMember, User, Category } from '../models/index.js';
import { recognizeReceipt } from '../services/aiService.js';
import multer from 'multer';
import { sequelize } from '../config/db.js';

const upload = multer({ storage: multer.memoryStorage() });

export const createExpense = async (req, res, next) => {
  const transaction = await sequelize.transaction();
  try {
    const { groupId, payerId, categoryId, amount, description, date, splits } = req.body;
    const membership = await GroupMember.findOne({ where: { groupId, userId: req.userId } });
    if (!membership) { await transaction.rollback(); return res.status(403).json({ message: 'Вы не состоите в этой группе' }); }

    let finalSplits = splits;
    if (!finalSplits) {
      const members = await GroupMember.findAll({ where: { groupId }, attributes: ['userId'] });
      const memberIds = members.map(m => m.userId);
      const share = amount / memberIds.length;
      finalSplits = memberIds.map(userId => ({ userId, amountOwed: share }));
    }

    const expense = await Expense.create({
      groupId, payerId, categoryId, amount, description, date: date ? new Date(date) : new Date(),
    }, { transaction });

    await ExpenseSplit.bulkCreate(finalSplits.map(s => ({
      expenseId: expense.id, userId: s.userId, amountOwed: s.amountOwed, isPaid: s.userId === payerId,
    })), { transaction });

    await transaction.commit();
    res.status(201).json(expense);
  } catch (err) { await transaction.rollback(); next(err); }
};

export const getExpenses = async (req, res, next) => {
  try {
    const { groupId } = req.params;
    const { from, to, categoryId, userId } = req.query;
    const where = { groupId };
    if (from || to) {
      where.date = {};
      if (from) where.date[Op.gte] = new Date(from);
      if (to) where.date[Op.lte] = new Date(to);
    }
    if (categoryId) where.categoryId = categoryId;
    if (userId) {
      const splits = await ExpenseSplit.findAll({ where: { userId }, attributes: ['expenseId'] });
      const expenseIds = splits.map(s => s.expenseId);
      where[Op.or] = [
        { payerId: userId },
        { id: { [Op.in]: expenseIds } },
      ];
    }

    const expenses = await Expense.findAll({
      where,
      include: [
        { model: User, as: 'payer', attributes: ['id', 'name'] },
        { model: Category, attributes: ['id', 'name', 'icon', 'color'] },
        { model: ExpenseSplit, as: 'ExpenseSplits', include: [{ model: User, attributes: ['id', 'name'] }] },
      ],
      order: [['date', 'DESC']],
    });
    res.json(expenses);
  } catch (err) { next(err); }
};

export const updateExpense = async (req, res, next) => {
  try {
    const expense = await Expense.findByPk(req.params.expenseId);
    if (!expense) return res.status(404).json({ message: 'Расход не найден' });
    const membership = await GroupMember.findOne({ where: { groupId: expense.groupId, userId: req.userId } });
    if (!membership) return res.status(403).json({ message: 'Нет прав' });
    await expense.update(req.body);
    res.json(expense);
  } catch (err) { next(err); }
};

export const deleteExpense = async (req, res, next) => {
  try {
    const expense = await Expense.findByPk(req.params.expenseId);
    if (!expense) return res.status(404).json({ message: 'Расход не найден' });
    const membership = await GroupMember.findOne({ where: { groupId: expense.groupId, userId: req.userId } });
    if (!membership) return res.status(403).json({ message: 'Нет прав' });
    await expense.destroy();
    res.json({ message: 'Расход удалён' });
  } catch (err) { next(err); }
};

export const uploadMiddleware = upload.single('photo');

export const uploadReceipt = async (req, res, next) => {
  try {
    if (!req.file) return res.status(400).json({ message: 'Файл не загружен' });
    const imageBuffer = req.file.buffer;
    const recognized = await recognizeReceipt(imageBuffer);
    res.json(recognized);
  } catch (err) { next(err); }
};