import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';
import User from './user.js';

const GroupMember = sequelize.define('GroupMember', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' } },
  userId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  role: { type: DataTypes.STRING, defaultValue: 'member' },
  joinedAt: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
});

GroupMember.addIndex(['groupId', 'userId'], { unique: true });

export default GroupMember;