/**
 * REQ-01 — Available slot grid picker.
 *
 * Displays a horizontal grid of "HH:MM" time buttons, allowing the user
 * to select one slot. Loading and empty states are built in.
 *
 * REQ-09: When no slots are available and onJoinWaitlist is provided,
 * shows a "Join Waitlist" button wired to the waitlist flow.
 */
import { Clock } from 'lucide-react';
import { SkeletonBlock } from './SkeletonBlock';

interface Props {
  /** Available slot strings in HH:MM format. */
  slots: string[];
  /** Currently selected slot (HH:MM) or empty string. */
  selected: string;
  /** Called when user clicks a slot button. */
  onSelect: (slot: string) => void;
  /** Show a loading skeleton while fetching. */
  loading?: boolean;
  /** True once doctor + date are both chosen so "no slots" can be shown. */
  ready?: boolean;
  /** REQ-09: Called when patient clicks "Join Waitlist". Omit to hide button. */
  onJoinWaitlist?: () => void;
  /** True while join-waitlist request is in flight. */
  joiningWaitlist?: boolean;
}

export function SlotPicker({
  slots,
  selected,
  onSelect,
  loading = false,
  ready = false,
  onJoinWaitlist,
  joiningWaitlist = false,
}: Props) {
  if (loading) {
    return <SkeletonBlock lines={2} />;
  }

  if (ready && slots.length === 0) {
    return (
      <div style={{ padding: '0.5rem 0' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            color: 'var(--color-text-light)',
            marginBottom: onJoinWaitlist ? '0.75rem' : 0,
          }}
          role="status"
        >
          <Clock size={16} aria-hidden="true" />
          No available slots for this date.
        </div>
        {onJoinWaitlist && (
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={onJoinWaitlist}
            disabled={joiningWaitlist}
            data-testid="join-waitlist-btn"
          >
            {joiningWaitlist ? 'Joining…' : 'Join Waitlist for this date'}
          </button>
        )}
      </div>
    );
  }

  if (slots.length === 0) return null;

  return (
    <div>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '0.5rem',
          marginTop: '0.25rem',
        }}
        role="listbox"
        aria-label="Available time slots"
      >
        {slots.map((slot) => (
          <button
            key={slot}
            type="button"
            role="option"
            aria-selected={selected === slot}
            className={`slot-btn${selected === slot ? ' slot-btn--selected' : ''}`}
            onClick={() => onSelect(selected === slot ? '' : slot)}
          >
            {slot}
          </button>
        ))}
      </div>
      {selected && (
        <p
          style={{
            marginTop: '0.4rem',
            fontSize: '0.85rem',
            color: 'var(--color-text-light)',
          }}
        >
          Selected: <strong>{selected}</strong>
        </p>
      )}
    </div>
  );
}
