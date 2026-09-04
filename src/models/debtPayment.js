import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Debt from './debt.js';

const DebtPayment = sequelize.define('DebtPayment', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  debtId: { type: DataTypes.UUID, references: { model: Debt, key: 'id' } },
  amount: { type: DataTypes.DECIMAL(10, 2), allowNull: false },
  createdAt: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
});

export default DebtPayment;