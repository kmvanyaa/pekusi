import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { User, Session } from '../models/index.js';
import { env } from '../config/env.js';

const createSession = async (userId) => {
  const token = jwt.sign({ userId }, env.jwtSecret, { expiresIn: '30d' });
  const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
  await Session.create({ userId, token, expiresAt });
  return token;
};

export const register = async (req, res, next) => {
  try {
    const { email, password, name, telegramId } = req.body;
    const existing = await User.findOne({ where: { email } });
    if (existing) return res.status(400).json({ message: 'Пользователь с таким email уже существует' });
    const passwordHash = await bcrypt.hash(password, 10);
    const user = await User.create({ email, passwordHash, name, telegramId });
    const accessToken = await createSession(user.id);
    res.status(201).json({ user: { id: user.id, email: user.email, name: user.name, telegramId }, accessToken });
  } catch (err) { next(err); }
};

export const login = async (req, res, next) => {
  try {
    const { email, password } = req.body;
    const user = await User.findOne({ where: { email } });
    if (!user) return res.status(401).json({ message: 'Неверный email или пароль' });
    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) return res.status(401).json({ message: 'Неверный email или пароль' });
    const accessToken = await createSession(user.id);
    res.json({ user: { id: user.id, email: user.email, name: user.name, telegramId: user.telegramId }, accessToken });
  } catch (err) { next(err); }
};

export const loginByTelegram = async (req, res, next) => {
  try {
    const { telegramId } = req.body;
    const user = await User.findOne({ where: { telegramId } });
    if (!user) return res.status(404).json({ message: 'Пользователь с таким Telegram ID не найден' });
    const accessToken = await createSession(user.id);
    res.json({ user: { id: user.id, email: user.email, name: user.name, telegramId }, accessToken });
  } catch (err) { next(err); }
};

export const linkTelegram = async (req, res, next) => {
  try {
    const { telegramId } = req.body;
    await User.update({ telegramId }, { where: { id: req.userId } });
    res.json({ message: 'Telegram привязан', telegramId });
  } catch (err) { next(err); }
};