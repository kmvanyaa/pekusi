import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';

const SavingsGoal = sequelize.define('SavingsGoal', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' } },
  name: { type: DataTypes.STRING, allowNull: false },
  type: { type: DataTypes.STRING, defaultValue: 'group' },
  targetAmount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  currentAmount: { type: DataTypes.DECIMAL(10, 2), defaultValue: 0 },
  createdBy: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  deadline: DataTypes.DATE,
  status: { type: DataTypes.STRING, defaultValue: 'active' },
});

export default SavingsGoal;