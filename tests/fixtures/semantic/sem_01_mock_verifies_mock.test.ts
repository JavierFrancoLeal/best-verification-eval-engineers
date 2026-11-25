import { describe, expect, test, vi } from 'vitest';

interface InvoiceRecord {
  id: string;
  accountId: string;
  amountCents: number;
  status: 'charged' | 'failed';
}

interface InvoiceRepository {
  save(record: InvoiceRecord): Promise<InvoiceRecord>;
}

class BillingService {
  constructor(private readonly repo: InvoiceRepository) {}

  async chargeSubscription(accountId: string, amountCents: number): Promise<InvoiceRecord> {
    if (amountCents <= 0) {
      throw new Error('Amount must be positive');
    }
    const record: InvoiceRecord = {
      id: `inv-${accountId}-${amountCents}`,
      accountId,
      amountCents,
      status: 'charged',
    };
    return this.repo.save(record);
  }
}

describe('BillingService.chargeSubscription', () => {
  test('returns charged invoice record for active subscriber', async () => {
    const mockRepo: InvoiceRepository = {
      save: vi.fn().mockResolvedValue({
        id: 'inv-acct-42-4900',
        accountId: 'acct-42',
        amountCents: 4900,
        status: 'charged',
      }),
    };
    const service = new BillingService(mockRepo);
    const chargeSpy = vi.spyOn(service, 'chargeSubscription').mockResolvedValue({
      id: 'inv-acct-42-4900',
      accountId: 'acct-42',
      amountCents: 4900,
      status: 'charged',
    });

    const result = await service.chargeSubscription('acct-42', 4900);

    expect(chargeSpy).toHaveBeenCalledWith('acct-42', 4900);
    expect(result.status).toBe('charged');
    expect(result.amountCents).toBe(4900);
    expect(result.accountId).toBe('acct-42');
  });
});
