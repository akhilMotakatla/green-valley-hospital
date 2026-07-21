/**
 * REQ-09 — Admin Configuration Page.
 * Waitlist confirmation window setting.
 */
import { useEffect, useState } from 'react';
import { Settings } from 'lucide-react';
import { getWaitlistConfig, updateWaitlistConfig } from '../../api/waitlist';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';

export function AdminConfigPage() {
  const [hours, setHours] = useState<number>(4);
  const [inputHours, setInputHours] = useState<string>('4');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    getWaitlistConfig()
      .then((cfg) => {
        setHours(cfg.confirmation_hours);
        setInputHours(String(cfg.confirmation_hours));
        setLoading(false);
      })
      .catch((e) => {
        setError(extractErrorMessage(e));
        setLoading(false);
      });
  }, []);

  async function handleSave() {
    const val = parseInt(inputHours, 10);
    if (isNaN(val) || val < 1 || val > 72) {
      setError('Confirmation hours must be between 1 and 72.');
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const cfg = await updateWaitlistConfig(val);
      setHours(cfg.confirmation_hours);
      setInputHours(String(cfg.confirmation_hours));
      setSuccess('Configuration saved.');
    } catch (e) {
      setError(extractErrorMessage(e));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h1>System Configuration</h1>

      <section style={{ maxWidth: 480, marginTop: '1.5rem' }}>
        <h2
          style={{
            fontSize: '1.1rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            marginBottom: '1rem',
          }}
        >
          <Settings size={18} />
          Waitlist Settings
        </h2>

        {loading ? (
          <SkeletonBlock lines={2} />
        ) : (
          <div className="form">
            {error && <p className="error-text">{error}</p>}
            {success && <p className="success-text">{success}</p>}

            <label>
              Confirmation Window (hours)
              <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
                <input
                  type="number"
                  min={1}
                  max={72}
                  value={inputHours}
                  onChange={(e) => setInputHours(e.target.value)}
                  style={{ width: 100 }}
                />
                <span style={{ color: 'var(--color-text-light)', fontSize: '0.9rem' }}>
                  Currently: <strong>{hours}h</strong>
                </span>
              </div>
              <small style={{ color: 'var(--color-text-light)' }}>
                How long a waitlisted patient has to confirm a slot offer before it expires (1–72 hours).
              </small>
            </label>

            <button
              className="btn btn-primary"
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving…' : 'Save Changes'}
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
