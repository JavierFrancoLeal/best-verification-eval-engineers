import { describe, expect, test } from 'vitest';

interface AuthContext {
  userId: string;
  tenantId: string;
}

interface TenantReport {
  reportId: string;
  tenantId: string;
  subtotalCents: number;
  taxBps: number;
}

interface HttpRequest {
  params: { tenantId: string; reportId: string };
  auth: AuthContext | null;
}

interface HttpResponse {
  status: number;
  body: Record<string, unknown>;
}

function computeGrossTotalCents(subtotalCents: number, taxBps: number): number {
  return subtotalCents + Math.round((subtotalCents * taxBps) / 10_000);
}

function handleGetTenantReport(
  req: HttpRequest,
  store: Map<string, TenantReport>
): HttpResponse {
  if (!req.auth) {
    return { status: 401, body: { error: 'unauthorized' } };
  }
  if (req.auth.tenantId !== req.params.tenantId) {
    return { status: 403, body: { error: 'forbidden_tenant_mismatch' } };
  }
  const report = store.get(req.params.reportId);
  if (!report) {
    return { status: 404, body: { error: 'not_found' } };
  }
  if (report.tenantId !== req.auth.tenantId) {
    return { status: 403, body: { error: 'forbidden_cross_tenant_object' } };
  }
  return {
    status: 200,
    body: {
      reportId: report.reportId,
      tenantId: report.tenantId,
      grossTotalCents: computeGrossTotalCents(report.subtotalCents, report.taxBps),
    },
  };
}

describe('TenantReport endpoint behavioral & authorization suite', () => {
  const inMemoryStore = new Map<string, TenantReport>([
    ['rpt-201', { reportId: 'rpt-201', tenantId: 'tenant-alpha', subtotalCents: 10_000, taxBps: 825 }],
    ['rpt-202', { reportId: 'rpt-202', tenantId: 'tenant-beta', subtotalCents: 25_000, taxBps: 500 }],
  ]);

  test('returns 200 OK with hand-verified gross total for owner tenant', () => {
    const response = handleGetTenantReport(
      {
        params: { tenantId: 'tenant-alpha', reportId: 'rpt-201' },
        auth: { userId: 'u-alpha', tenantId: 'tenant-alpha' },
      },
      inMemoryStore
    );

    expect(response.status).toBe(200);
    expect(response.body.grossTotalCents).toBe(10_825);
  });

  test('returns 403 Forbidden when tenant-beta requests tenant-alpha report', () => {
    const response = handleGetTenantReport(
      {
        params: { tenantId: 'tenant-beta', reportId: 'rpt-201' },
        auth: { userId: 'u-beta', tenantId: 'tenant-beta' },
      },
      inMemoryStore
    );

    expect(response.status).toBe(403);
    expect(response.body.error).toBe('forbidden_cross_tenant_object');
    expect(response.body.grossTotalCents).toBeUndefined();
  });

  test('returns 403 Forbidden when route tenantId mismatches auth context', () => {
    const response = handleGetTenantReport(
      {
        params: { tenantId: 'tenant-alpha', reportId: 'rpt-201' },
        auth: { userId: 'u-beta', tenantId: 'tenant-beta' },
      },
      inMemoryStore
    );

    expect(response.status).toBe(403);
    expect(response.body.error).toBe('forbidden_tenant_mismatch');
  });

  test('returns 401 Unauthorized when caller lacks authentication context', () => {
    const response = handleGetTenantReport(
      {
        params: { tenantId: 'tenant-alpha', reportId: 'rpt-201' },
        auth: null,
      },
      inMemoryStore
    );

    expect(response.status).toBe(401);
    expect(response.body.error).toBe('unauthorized');
  });
});
