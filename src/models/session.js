import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import User from './user.js';

const Session = sequelize.define('Session', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  userId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  token: { type: DataTypes.STRING, unique: true },
  expiresAt: { type: DataTypes.DATE, allowNull: false },
  createdAt: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
});

export default Session;