import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

function mulberry32(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) >>> 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function scheduleRetry(delayMs: number, onTrigger: () => void): ReturnType<typeof setTimeout> {
  return setTimeout(onTrigger, delayMs);
}

describe('deterministic retry scheduler', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-11-24T12:00:00Z'));
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('triggers callback at exact fake-timer boundary', () => {
    const callback = vi.fn();
    scheduleRetry(500, callback);

    vi.advanceTimersByTime(499);
    expect(callback).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(callback).toHaveBeenCalledTimes(1);
  });

  test('produces reproducible jitter values from seeded PRNG', () => {
    const prngA = mulberry32(20261124);
    const prngB = mulberry32(20261124);
    const seqA = [prngA(), prngA(), prngA()];
    const seqB = [prngB(), prngB(), prngB()];

    expect(seqA).toEqual(seqB);
    expect(seqA[0]).toBeGreaterThanOrEqual(0);
    expect(seqA[0]).toBeLessThan(1);
  });
});
