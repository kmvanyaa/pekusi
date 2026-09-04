import { Expense, ExpenseSplit } from '../models/index.js';

export const calculateGroupDebts = async (groupId) => {
  const expenses = await Expense.findAll({
    where: { groupId },
    include: [{ model: ExpenseSplit, as: 'ExpenseSplits' }],
  });

  const balances = {};
  for (const expense of expenses) {
    const payerId = expense.payerId;
    if (!balances[payerId]) balances[payerId] = { paid: 0, owed: 0 };
    balances[payerId].paid += parseFloat(expense.amount);
    for (const split of expense.ExpenseSplits) {
      if (!balances[split.userId]) balances[split.userId] = { paid: 0, owed: 0 };
      balances[split.userId].owed += parseFloat(split.amountOwed);
    }
  }

  const creditors = [], debtors = [];
  for (const [userId, bal] of Object.entries(balances)) {
    const net = bal.paid - bal.owed;
    if (net > 0) creditors.push({ userId, net });
    else if (net < 0) debtors.push({ userId, net: -net });
  }

  const debts = [];
  let i = 0, j = 0;
  while (i < debtors.length && j < creditors.length) {
    const debtor = debtors[i], creditor = creditors[j];
    const amount = Math.min(debtor.net, creditor.net);
    debts.push({ fromUserId: debtor.userId, toUserId: creditor.userId, amount });
    debtor.net -= amount; creditor.net -= amount;
    if (debtor.net === 0) i++;
    if (creditor.net === 0) j++;
  }
  return debts;
};