import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';
import Category from './category.js';

const Expense = sequelize.define('Expense', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' } },
  payerId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  categoryId: { type: DataTypes.UUID, references: { model: Category, key: 'id' } },
  amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  description: DataTypes.TEXT,
  date: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
  receiptPhotoUrl: DataTypes.STRING,
});

export default Expense;