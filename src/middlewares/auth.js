import jwt from 'jsonwebtoken';
import { Session } from '../models/index.js';
import { env } from '../config/env.js';

export const auth = async (req, res, next) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    if (!token) return res.status(401).json({ message: 'Требуется авторизация' });

    let decoded;
    try {
      decoded = jwt.verify(token, env.jwtSecret);
    } catch (err) {
      return res.status(401).json({ message: 'Недействительный токен' });
    }

    const session = await Session.findOne({ where: { token } });
    if (!session || session.expiresAt < new Date()) {
      return res.status(401).json({ message: 'Сессия не найдена или истекла' });
    }

    req.userId = decoded.userId;
    next();
  } catch (err) {
    return res.status(401).json({ message: 'Недействительный токен' });
  }
};