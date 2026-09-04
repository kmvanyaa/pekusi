export const errorHandler = (err, req, res, next) => {
  console.error(err);
  if (err.name === 'ZodError') {
    return res.status(400).json({ message: 'Ошибка валидации', errors: err.errors });
  }
  res.status(err.status || 500).json({ message: err.message || 'Внутренняя ошибка сервера' });
};