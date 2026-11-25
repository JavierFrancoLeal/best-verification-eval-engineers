import { describe, expect, test } from 'vitest';

interface AuthContext {
  userId: string;
  tenantId: string;
  role: 'member' | 'admin';
}

interface TenantReport {
  reportId: string;
  tenantId: string;
  title: string;
  totalRevenueCents: number;
}

interface HttpRequest {
  params: { tenantId: string; reportId: string };
  auth: AuthContext | null;
}

interface HttpResponse {
  status: number;
  body: Record<string, unknown>;
}

// Endpoint: GET /api/v1/tenants/:tenantId/reports/:reportId
function handleGetTenantReport(
  req: HttpRequest,
  reportStore: Map<string, TenantReport>
): HttpResponse {
  if (!req.auth) {
    return { status: 401, body: { error: 'unauthorized' } };
  }
  const report = reportStore.get(req.params.reportId);
  if (!report) {
    return { status: 404, body: { error: 'not_found' } };
  }
  return {
    status: 200,
    body: {
      reportId: report.reportId,
      tenantId: report.tenantId,
      title: report.title,
      totalRevenueCents: report.totalRevenueCents,
    },
  };
}

describe('GET /api/v1/tenants/:tenantId/reports/:reportId', () => {
  const store = new Map<string, TenantReport>([
    [
      'rpt-101',
      {
        reportId: 'rpt-101',
        tenantId: 'tenant-alpha',
        title: 'Q3 Financial Summary',
        totalRevenueCents: 1_250_000,
      },
    ],
  ]);

  test('returns 200 OK with report payload for authenticated tenant member', () => {
    const response = handleGetTenantReport(
      {
        params: { tenantId: 'tenant-alpha', reportId: 'rpt-101' },
        auth: { userId: 'user-1', tenantId: 'tenant-alpha', role: 'member' },
      },
      store
    );

    expect(response.status).toBe(200);
    expect(response.body.reportId).toBe('rpt-101');
    expect(response.body.title).toBe('Q3 Financial Summary');
    expect(response.body.totalRevenueCents).toBe(1_250_000);
  });

  test('returns 404 Not Found when report identifier does not exist', () => {
    const response = handleGetTenantReport(
      {
        params: { tenantId: 'tenant-alpha', reportId: 'rpt-missing' },
        auth: { userId: 'user-1', tenantId: 'tenant-alpha', role: 'member' },
      },
      store
    );

    expect(response.status).toBe(404);
    expect(response.body.error).toBe('not_found');
  });
});
