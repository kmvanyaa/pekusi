import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import User from './user.js';
import Achievement from './achievement.js';

const UserAchievement = sequelize.define('UserAchievement', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  userId: { type: DataTypes.UUID, references: { model: User, key: 'id' } },
  achievementId: { type: DataTypes.UUID, references: { model: Achievement, key: 'id' } },
  earnedAt: { type: DataTypes.DATE, defaultValue: DataTypes.NOW },
});

UserAchievement.addIndex(['userId', 'achievementId'], { unique: true });

export default UserAchievement;