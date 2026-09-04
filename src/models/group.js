import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import User from './user.js';

const Group = sequelize.define('Group', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  currency: { type: DataTypes.STRING, defaultValue: 'RUB' },
  inviteCode: { type: DataTypes.STRING, unique: true },
  ownerId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
});

export default Group;