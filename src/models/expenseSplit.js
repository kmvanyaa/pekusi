import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Expense from './expense.js';
import User from './user.js';

const ExpenseSplit = sequelize.define('ExpenseSplit', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  expenseId: { type: DataTypes.UUID, references: { model: Expense, key: 'id' } },
  userId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  amountOwed: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  isPaid: { type: DataTypes.BOOLEAN, defaultValue: false },
});

ExpenseSplit.addIndex(['expenseId', 'userId'], { unique: true });

export default ExpenseSplit;