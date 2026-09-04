import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';

const Achievement = sequelize.define('Achievement', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: DataTypes.STRING,
  description: DataTypes.TEXT,
  icon: DataTypes.STRING,
  condition: DataTypes.TEXT,
});

export default Achievement;