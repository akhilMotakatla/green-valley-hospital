/**
 * REQ-01 — Weekly availability schedule editor.
 *
 * Renders a 7-row grid (Mon–Sun). Each row shows the doctor's scheduled
 * availability windows for that day. Supports add, activate/deactivate,
 * and delete for each window. Also includes slot-duration config at top.
 */
import { useState } from 'react';
import { Check, Clock, Plus, Trash2, X } from 'lucide-react';
import type { AvailabilitySchedule, SlotConfig } from '../api/availability';
import { extractErrorMessage } from '../api/client';

const DAY_NAMES = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
];

const SLOT_DURATIONS = [10, 15, 20, 30, 45, 60];

interface Props {
  schedules: AvailabilitySchedule[];
  config: SlotConfig;
  onAddWindow: (dayOfWeek: number, startTime: string, endTime: string) => Promise<void>;
  onToggleActive: (scheduleId: number, isActive: boolean) => Promise<void>;
  onDeleteWindow: (scheduleId: number) => Promise<void>;
  onUpdateConfig: (slotDurationMinutes: number) => Promise<void>;
  /** When true, all editing controls are hidden (read-only display mode). */
  readOnly?: boolean;
}

export function AvailabilityWeekGrid({
  schedules,
  config,
  onAddWindow,
  onToggleActive,
  onDeleteWindow,
  onUpdateConfig,
  readOnly = false,
}: Props) {
  const [addingDay, setAddingDay] = useState<number | null>(null);
  const [newStart, setNewStart] = useState('09:00');
  const [newEnd, setNewEnd] = useState('17:00');
  const [addError, setAddError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  const [slotDuration, setSlotDuration] = useState<number>(config.slot_duration_minutes);
  const [configBusy, setConfigBusy] = useState(false);

  const windowsForDay = (day: number) =>
    schedules.filter((s) => s.day_of_week === day);

  async function handleAdd() {
    if (addingDay === null) return;
    setAddError(null);
    try {
      await onAddWindow(addingDay, newStart, newEnd);
      setAddingDay(null);
    } catch (e) {
      setAddError(extractErrorMessage(e));
    }
  }

  async function handleDelete(id: number) {
    setBusyId(id);
    try {
      await onDeleteWindow(id);
    } finally {
      setBusyId(null);
    }
  }

  async function handleToggle(id: number, currentActive: boolean) {
    setBusyId(id);
    try {
      await onToggleActive(id, !currentActive);
    } finally {
      setBusyId(null);
    }
  }

  async function handleSaveConfig() {
    setConfigBusy(true);
    try {
      await onUpdateConfig(slotDuration);
    } finally {
      setConfigBusy(false);
    }
  }

  return (
    <div className="availability-grid">
      {/* Slot duration row */}
      <div className="availability-config-row">
        <Clock size={15} aria-hidden="true" />
        <span className="availability-config-label">Slot duration</span>
        <select
          value={slotDuration}
          onChange={(e) => setSlotDuration(Number(e.target.value))}
          disabled={readOnly}
          aria-label="Slot duration in minutes"
        >
          {SLOT_DURATIONS.map((m) => (
            <option key={m} value={m}>
              {m} min
            </option>
          ))}
        </select>
        {!readOnly && slotDuration !== config.slot_duration_minutes && (
          <button
            className="btn btn-primary btn-sm"
            onClick={handleSaveConfig}
            disabled={configBusy}
          >
            {configBusy ? 'Saving…' : 'Save'}
          </button>
        )}
        {!readOnly && slotDuration !== config.slot_duration_minutes && (
          <button
            className="btn btn-outline btn-sm"
            onClick={() => setSlotDuration(config.slot_duration_minutes)}
            disabled={configBusy}
          >
            Reset
          </button>
        )}
      </div>

      {/* Day rows */}
      <div className="availability-days">
        {DAY_NAMES.map((dayName, dayIndex) => {
          const windows = windowsForDay(dayIndex);
          const isAddingThisDay = addingDay === dayIndex;
          return (
            <div key={dayIndex} className="availability-day-row">
              <div className="availability-day-label">{dayName}</div>

              <div className="availability-day-content">
                {windows.length === 0 && (
                  <span className="availability-off-badge">Off</span>
                )}

                <div className="availability-chips">
                  {windows.map((w) => (
                    <div
                      key={w.schedule_id}
                      className={`availability-chip ${!w.is_active ? 'availability-chip--inactive' : ''}`}
                    >
                      <span className="chip-time">
                        {w.start_time}&ndash;{w.end_time}
                      </span>
                      {!w.is_active && (
                        <span className="chip-inactive-label">off</span>
                      )}
                      {!readOnly && (
                        <div className="chip-actions">
                          <button
                            className="chip-btn"
                            title={w.is_active ? 'Deactivate window' : 'Activate window'}
                            aria-label={w.is_active ? 'Deactivate' : 'Activate'}
                            disabled={busyId === w.schedule_id}
                            onClick={() => handleToggle(w.schedule_id, w.is_active)}
                          >
                            {w.is_active ? <X size={11} /> : <Check size={11} />}
                          </button>
                          <button
                            className="chip-btn chip-btn--danger"
                            title="Delete window"
                            aria-label="Delete window"
                            disabled={busyId === w.schedule_id}
                            onClick={() => handleDelete(w.schedule_id)}
                          >
                            <Trash2 size={11} />
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {!readOnly && !isAddingThisDay && (
                  <button
                    className="btn btn-outline btn-sm availability-add-btn"
                    onClick={() => {
                      setAddingDay(dayIndex);
                      setAddError(null);
                      setNewStart('09:00');
                      setNewEnd('17:00');
                    }}
                  >
                    <Plus size={12} />
                    Add window
                  </button>
                )}

                {isAddingThisDay && (
                  <div className="availability-add-form">
                    <input
                      type="time"
                      value={newStart}
                      onChange={(e) => setNewStart(e.target.value)}
                      aria-label="Window start time"
                    />
                    <span className="time-sep">to</span>
                    <input
                      type="time"
                      value={newEnd}
                      onChange={(e) => setNewEnd(e.target.value)}
                      aria-label="Window end time"
                    />
                    <button className="btn btn-primary btn-sm" onClick={handleAdd}>
                      Save
                    </button>
                    <button
                      className="btn btn-outline btn-sm"
                      onClick={() => setAddingDay(null)}
                    >
                      Cancel
                    </button>
                    {addError && (
                      <span className="form-error" role="alert">
                        {addError}
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
