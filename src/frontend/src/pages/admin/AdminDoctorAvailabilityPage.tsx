/**
 * REQ-01 — Admin override: view and edit any doctor's availability.
 * Route: /admin/users/:userId/availability
 * Reached via the "Schedule" button on AdminUsersPage doctor rows.
 *
 * Loads the user record first to resolve profile.doctor_id, then uses
 * admin-scoped availability endpoints (/admin/doctors/{doctorId}/availability/*).
 */
import { useCallback, useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { ArrowLeft, CalendarClock, ShieldAlert } from 'lucide-react';
import { Link, useParams } from 'react-router-dom';
import { getUser } from '../../api/admin';
import {
  adminCreateBlock,
  adminCreateScheduleWindow,
  adminDeleteBlock,
  adminDeleteScheduleWindow,
  adminGetBlocks,
  adminGetSchedule,
  adminGetSlotConfig,
  adminUpdateScheduleWindow,
  adminUpdateSlotConfig,
} from '../../api/availability';
import type { AvailabilityBlock, AvailabilitySchedule, SlotConfig } from '../../api/availability';
import { AvailabilityWeekGrid } from '../../components/AvailabilityWeekGrid';
import { PageError } from '../../components/PageError';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { extractErrorMessage } from '../../api/client';

export function AdminDoctorAvailabilityPage() {
  const { userId } = useParams<{ userId: string }>();
  const uid = Number(userId);

  const [doctorId, setDoctorId] = useState<number | null>(null);
  const [doctorName, setDoctorName] = useState<string>('');
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
  const [deletingBlockId, setDeletingBlockId] = useState<number | null>(null);

  const load = useCallback(async () => {
    if (!uid) return;
    setLoading(true);
    setError(null);
    try {
      // Resolve user → doctor_id
      const user = await getUser(uid);
      if (user.role !== 'Doctor' || !user.profile?.doctor_id) {
        setError('This user does not have a Doctor profile.');
        setLoading(false);
        return;
      }
      const did: number = user.profile.doctor_id;
      setDoctorId(did);
      setDoctorName(user.full_name);

      const [sc, cfg, bl] = await Promise.all([
        adminGetSchedule(did),
        adminGetSlotConfig(did),
        adminGetBlocks(did),
      ]);
      setSchedules(sc);
      setConfig(cfg);
      setBlocks(bl);
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [uid]);

  useEffect(() => {
    load();
  }, [load]);

  // --- Grid callbacks (admin API) ---

  async function handleAddWindow(dayOfWeek: number, startTime: string, endTime: string) {
    if (!doctorId) return;
    await adminCreateScheduleWindow(doctorId, {
      day_of_week: dayOfWeek,
      start_time: startTime,
      end_time: endTime,
    });
    setSchedules(await adminGetSchedule(doctorId));
  }

  async function handleToggleActive(scheduleId: number, isActive: boolean) {
    if (!doctorId) return;
    await adminUpdateScheduleWindow(doctorId, scheduleId, { is_active: isActive });
    setSchedules(await adminGetSchedule(doctorId));
  }

  async function handleDeleteWindow(scheduleId: number) {
    if (!doctorId) return;
    await adminDeleteScheduleWindow(doctorId, scheduleId);
    setSchedules(await adminGetSchedule(doctorId));
  }

  async function handleUpdateConfig(slotDuration: number) {
    if (!doctorId) return;
    const updated = await adminUpdateSlotConfig(doctorId, slotDuration);
    setConfig(updated);
  }

  // --- Block form ---

  async function handleAddBlock(e: FormEvent) {
    e.preventDefault();
    if (!doctorId) return;
    setBlockBusy(true);
    setBlockError(null);
    try {
      await adminCreateBlock(doctorId, {
        block_date: blockDate,
        start_time: blockFullDay ? null : blockStart || null,
        end_time: blockFullDay ? null : blockEnd || null,
        reason: blockReason || null,
      });
      setBlockDate('');
      setBlockStart('');
      setBlockEnd('');
      setBlockReason('');
      setBlocks(await adminGetBlocks(doctorId));
    } catch (err) {
      setBlockError(extractErrorMessage(err));
    } finally {
      setBlockBusy(false);
    }
  }

  async function handleDeleteBlock(blockId: number) {
    if (!doctorId) return;
    setDeletingBlockId(blockId);
    try {
      await adminDeleteBlock(doctorId, blockId);
      setBlocks(await adminGetBlocks(doctorId));
    } finally {
      setDeletingBlockId(null);
    }
  }

  if (loading) return <SkeletonBlock lines={10} />;
  if (error) return <PageError message={error} onRetry={load} />;

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          marginBottom: '1.5rem',
        }}
      >
        <Link to="/admin/users" className="btn btn-outline btn-sm">
          <ArrowLeft size={14} aria-hidden="true" />
          Back to Users
        </Link>
        <h1 style={{ margin: 0 }}>
          Availability Override — {doctorName}
        </h1>
      </div>

      <p style={{ color: 'var(--color-text-light)', marginBottom: '1.5rem' }}>
        Admin override: edit this doctor&apos;s weekly availability schedule and date-specific
        blocks. Changes take effect immediately for slot queries.
      </p>

      {config && doctorId && (
        <AvailabilityWeekGrid
          schedules={schedules}
          config={config}
          onAddWindow={handleAddWindow}
          onToggleActive={handleToggleActive}
          onDeleteWindow={handleDeleteWindow}
          onUpdateConfig={handleUpdateConfig}
        />
      )}

      <hr
        style={{
          margin: '2rem 0',
          border: 'none',
          borderTop: '1px solid var(--color-border)',
        }}
      />

      {/* Date-specific blocks */}
      <section>
        <h2
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '0.5rem',
          }}
        >
          <ShieldAlert size={20} aria-hidden="true" />
          Date-Specific Overrides
        </h2>
        <p style={{ color: 'var(--color-text-light)', marginBottom: '1.25rem' }}>
          Block a specific date entirely or during a time range.
        </p>

        <form
          className="form"
          onSubmit={handleAddBlock}
          style={{ maxWidth: '640px' }}
        >
          <div
            className="form-row"
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '0.75rem',
              alignItems: 'flex-end',
            }}
          >
            <label style={{ flex: '1 1 140px' }}>
              Date
              <input
                type="date"
                value={blockDate}
                onChange={(e) => setBlockDate(e.target.value)}
                required
              />
            </label>

            <label
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                flex: '0 0 auto',
                paddingBottom: '4px',
              }}
            >
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
                    {b.start_time
                      ? `${b.start_time} – ${b.end_time}`
                      : 'All day'}
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
