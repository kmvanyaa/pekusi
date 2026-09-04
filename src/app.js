import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import swaggerJsdoc from 'swagger-jsdoc';
import swaggerUi from 'swagger-ui-express';

import { sequelize, ensureDatabaseExists } from './config/db.js';
import './models/index.js'; // инициализация моделей и связей

import authRoutes from './routes/auth.js';
import groupRoutes from './routes/groups.js';
import expenseRoutes from './routes/expenses.js';
import debtRoutes from './routes/debts.js';
import savingsGoalRoutes from './routes/savingsGoals.js';
import analyticsRoutes from './routes/analytics.js';
import categoryRoutes from './routes/categories.js';

import { auth } from './middlewares/auth.js';
import { errorHandler } from './middlewares/errorHandler.js';
import { env } from './config/env.js';

const app = express();

// Swagger настройка
const swaggerOptions = {
  definition: {
    openapi: '3.0.0',
    info: { title: 'Общак API', version: '1.0.0', description: 'API для сервиса совместных финансов «Общак»' },
    servers: [{ url: `http://localhost:${env.port}` }],
  },
  apis: ['./src/routes/*.js'],
};
const swaggerSpec = swaggerJsdoc(swaggerOptions);
app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

app.use(helmet());
app.use(cors({ origin: env.frontendUrl, credentials: true }));
app.use(express.json({ limit: '10mb' }));
app.use(morgan('dev'));

app.use('/api/auth', authRoutes);
app.use('/api/groups', auth, groupRoutes);
app.use('/api/expenses', auth, expenseRoutes);
app.use('/api/debts', auth, debtRoutes);
app.use('/api/savings-goals', auth, savingsGoalRoutes);
app.use('/api/analytics', auth, analyticsRoutes);
app.use('/api/categories', auth, categoryRoutes);

app.use(errorHandler);

// Инициализация БД
const init = async () => {
  await ensureDatabaseExists();
  await sequelize.authenticate();
  console.log('Подключение к MS SQL установлено');
  await sequelize.sync({ alter: true });
  console.log('Таблицы синхронизированы');
};

init().catch(err => {
  console.error('Ошибка инициализации БД:', err);
  process.exit(1);
});

export default app;