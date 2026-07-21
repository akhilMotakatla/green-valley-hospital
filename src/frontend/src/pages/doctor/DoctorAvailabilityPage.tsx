/**
 * REQ-01 — Doctor self-service availability management.
 * Route: /doctor/availability
 */
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { CalendarClock, ShieldAlert } from 'lucide-react';
import {
  createBlock,
  createScheduleWindow,
  deleteBlock,
  deleteScheduleWindow,
  getMyBlocks,
  getMySchedule,
  getMySlotConfig,
  updateMySlotConfig,
  updateScheduleWindow,
} from '../../api/availability';
import type { AvailabilityBlock, AvailabilitySchedule, SlotConfig } from '../../api/availability';
import { AvailabilityWeekGrid } from '../../components/AvailabilityWeekGrid';
import { PageError } from '../../components/PageError';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { extractErrorMessage } from '../../api/client';

export function DoctorAvailabilityPage() {
  const [schedules, setSchedules] = useState<AvailabilitySchedule[]>([]);
  const [config, setConfig] = useState<SlotConfig | null>(null);
  const [blocks, setBlocks] = useState<AvailabilityBlock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Block add form
  const [blockDate, setBlockDate] = useState('');
  const [blockFullDay, setBlockFullDay] = useState(true);
  const [blockStart, setBlockStart] = useState('');
  const [blockEnd, setBlockEnd] = useState('');
  const [blockReason, setBlockReason] = useState('');
  const [blockBusy, setBlockBusy] = useState(false);
  const [blockError, setBlockError] = useState<string | null>(null);
  const [blockSuccess, setBlockSuccess] = useState(false);
  const [deletingBlockId, setDeletingBlockId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [sc, cfg, bl] = await Promise.all([
        getMySchedule(),
        getMySlotConfig(),
        getMyBlocks(),
      ]);
      setSchedules(sc);
      setConfig(cfg);
      setBlocks(bl);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  // --- Grid callbacks ---

  async function handleAddWindow(dayOfWeek: number, startTime: string, endTime: string) {
    await createScheduleWindow({ day_of_week: dayOfWeek, start_time: startTime, end_time: endTime });
    setSchedules(await getMySchedule());
  }

  async function handleToggleActive(scheduleId: number, isActive: boolean) {
    await updateScheduleWindow(scheduleId, { is_active: isActive });
    setSchedules(await getMySchedule());
  }

  async function handleDeleteWindow(scheduleId: number) {
    await deleteScheduleWindow(scheduleId);
    setSchedules(await getMySchedule());
  }

  async function handleUpdateConfig(slotDuration: number) {
    const updated = await updateMySlotConfig(slotDuration);
    setConfig(updated);
  }

  // --- Block form ---

  async function handleAddBlock(e: FormEvent) {
    e.preventDefault();
    setBlockBusy(true);
    setBlockError(null);
    setBlockSuccess(false);
    try {
      await createBlock({
        block_date: blockDate,
        start_time: blockFullDay ? null : blockStart || null,
        end_time: blockFullDay ? null : blockEnd || null,
        reason: blockReason || null,
      });
      setBlockDate('');
      setBlockStart('');
      setBlockEnd('');
      setBlockReason('');
      setBlockSuccess(true);
      setBlocks(await getMyBlocks());
    } catch (err) {
      setBlockError(extractErrorMessage(err));
    } finally {
      setBlockBusy(false);
    }
  }

  async function handleDeleteBlock(blockId: number) {
    setDeletingBlockId(blockId);
    try {
      await deleteBlock(blockId);
      setBlocks(await getMyBlocks());
    } finally {
      setDeletingBlockId(null);
    }
  }

  if (loading) return <SkeletonBlock lines={10} />;
  if (error) return <PageError message={error} onRetry={load} />;

  return (
    <div>
      <h1>My Availability Schedule</h1>
      <p style={{ color: 'var(--color-text-light)', marginBottom: '1.5rem' }}>
        Set your weekly availability windows. Patients can only book slots within these windows.
        Use date-specific overrides below to block individual dates (e.g. leave, conferences).
      </p>

      {config && (
        <AvailabilityWeekGrid
          schedules={schedules}
          config={config}
          onAddWindow={handleAddWindow}
          onToggleActive={handleToggleActive}
          onDeleteWindow={handleDeleteWindow}
          onUpdateConfig={handleUpdateConfig}
        />
      )}

      <hr style={{ margin: '2rem 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />

      {/* Date-specific blocks */}
      <section>
        <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
          <ShieldAlert size={20} aria-hidden="true" />
          Date-Specific Overrides
        </h2>
        <p style={{ color: 'var(--color-text-light)', marginBottom: '1.25rem' }}>
          Block a specific date entirely or during a time range. Blocks override the weekly schedule.
        </p>

        <form className="form" onSubmit={handleAddBlock} style={{ maxWidth: '640px' }}>
          <div className="form-row" style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'flex-end' }}>
            <label style={{ flex: '1 1 140px' }}>
              Date
              <input
                type="date"
                value={blockDate}
                onChange={(e) => { setBlockDate(e.target.value); setBlockSuccess(false); }}
                required
              />
            </label>

            <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: '0 0 auto', paddingBottom: '4px' }}>
              <input
                type="checkbox"
                checked={blockFullDay}
                onChange={(e) => setBlockFullDay(e.target.checked)}
              />
              Full day
            </label>

            {!blockFullDay && (
              <>
                <label style={{ flex: '1 1 100px' }}>
                  From
                  <input
                    type="time"
                    value={blockStart}
                    onChange={(e) => setBlockStart(e.target.value)}
                    required={!blockFullDay}
                  />
                </label>
                <label style={{ flex: '1 1 100px' }}>
                  To
                  <input
                    type="time"
                    value={blockEnd}
                    onChange={(e) => setBlockEnd(e.target.value)}
                    required={!blockFullDay}
                  />
                </label>
              </>
            )}

            <label style={{ flex: '2 1 200px' }}>
              Reason (optional)
              <input
                type="text"
                value={blockReason}
                placeholder="e.g. Conference, Leave"
                onChange={(e) => setBlockReason(e.target.value)}
              />
            </label>
          </div>

          {blockError && (
            <p className="error-text" role="alert" style={{ marginTop: '0.5rem' }}>
              {blockError}
            </p>
          )}
          {blockSuccess && (
            <p className="success-text" style={{ marginTop: '0.5rem' }}>
              Block added successfully.
            </p>
          )}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={blockBusy}
            style={{ marginTop: '0.75rem' }}
          >
            {blockBusy ? 'Adding…' : 'Add Block'}
          </button>
        </form>

        {blocks.length === 0 ? (
          <div
            className="empty-state"
            style={{ padding: '1.5rem 0', textAlign: 'center' }}
          >
            <CalendarClock size={48} color="var(--color-text-light)" aria-hidden="true" />
            <p style={{ color: 'var(--color-text-light)', marginTop: '0.5rem' }}>
              No date-specific overrides set
            </p>
          </div>
        ) : (
          <table className="data-table" style={{ marginTop: '1.25rem' }}>
            <thead>
              <tr>
                <th>Date</th>
                <th>Scope</th>
                <th>Time range</th>
                <th>Reason</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {blocks.map((b) => (
                <tr key={b.block_id}>
                  <td>{b.block_date}</td>
                  <td>{b.start_time ? 'Partial' : 'Full day'}</td>
                  <td>
                    {b.start_time ? `${b.start_time} – ${b.end_time}` : 'All day'}
                  </td>
                  <td>{b.reason ?? '—'}</td>
                  <td>
                    <button
                      className="btn btn-danger btn-sm"
                      disabled={deletingBlockId === b.block_id}
                      onClick={() => handleDeleteBlock(b.block_id)}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
