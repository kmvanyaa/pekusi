import { DataTypes } from 'sequelize';
import { sequelize } from '../config/db.js';
import Group from './group.js';

const Category = sequelize.define('Category', {
  id: { type: DataTypes.UUID, defaultValue: DataTypes.UUIDV4, primaryKey: true },
  name: { type: DataTypes.STRING, allowNull: false },
  icon: DataTypes.STRING,
  color: DataTypes.STRING,
  isDefault: { type: DataTypes.BOOLEAN, defaultValue: false },
  groupId: { type: DataTypes.UUID, references: { model: Group, key: 'id' } },
});

export default Category;