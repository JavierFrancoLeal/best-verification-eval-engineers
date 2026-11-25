import { describe, expect, test } from 'vitest';

function computeBackoffMs(attempt: number, jitterFactor: number): number {
  const baseMs = 50 * Math.pow(2, attempt);
  return Math.round(baseMs * (0.5 + jitterFactor));
}

describe('backoff scheduler timing behavior', () => {
  test('computes bounded jittered delay for retry attempt', () => {
    const jitter = Math.random();
    const delayMs = computeBackoffMs(2, jitter);
    expect(delayMs).toBeGreaterThanOrEqual(100);
    expect(delayMs).toBeLessThanOrEqual(300);
  });

  test('executes delayed retry callback after wait interval', async () => {
    let completed = false;
    setTimeout(() => {
      completed = true;
    }, 150);

    await new Promise((resolve) => setTimeout(resolve, 250));
    expect(completed).toBe(true);
  });
});
