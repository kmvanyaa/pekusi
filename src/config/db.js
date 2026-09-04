import { Sequelize } from 'sequelize';
import { env } from './env.js';

// Функция для создания базы данных, если её нет
const ensureDatabaseExists = async () => {
  const masterSequelize = new Sequelize('master', env.mssql.user, env.mssql.password, {
    host: env.mssql.host,
    port: env.mssql.port,
    dialect: 'mssql',
    dialectOptions: {
      options: {
        encrypt: false,
        trustServerCertificate: true,
      },
    },
    logging: false,
  });

  try {
    await masterSequelize.query(`
      IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'${env.mssql.database}')
      BEGIN
        CREATE DATABASE [${env.mssql.database}];
      END
    `);
    console.log(`База данных ${env.mssql.database} готова`);
  } catch (err) {
    console.error('Ошибка при создании базы данных:', err);
    throw err;
  } finally {
    await masterSequelize.close();
  }
};

// Основное подключение
const sequelize = new Sequelize(env.mssql.database, env.mssql.user, env.mssql.password, {
  host: env.mssql.host,
  port: env.mssql.port,
  dialect: 'mssql',
  dialectOptions: {
    options: {
      encrypt: false,
      trustServerCertificate: true,
    },
  },
  logging: false,
  define: {
    freezeTableName: true,
    timestamps: true,
  },
});

export { sequelize, ensureDatabaseExists };