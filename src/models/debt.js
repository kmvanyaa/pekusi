import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';

const Debt = sequelize.define('Debt', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' } },
  fromUserId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  toUserId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  status: { type: DataTypes.STRING, defaultValue: 'pending' },
});

export default Debt;