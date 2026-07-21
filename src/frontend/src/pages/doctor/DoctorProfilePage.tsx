import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { getMyDoctorProfile, updateMyDoctorProfile, type DoctorProfile } from '../../api/doctor';
import { extractErrorMessage } from '../../api/client';
import { SkeletonBlock } from '../../components/SkeletonBlock';
import { PageError } from '../../components/PageError';

export function DoctorProfilePage() {
  const [profile, setProfile] = useState<DoctorProfile | null>(null);
  const [bio, setBio] = useState('');
  const [qualifications, setQualifications] = useState('');
  const [hours, setHours] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getMyDoctorProfile()
      .then((p) => {
        setProfile(p);
        setBio(p.bio ?? '');
        setQualifications(p.qualifications ?? '');
        setHours(p.consultation_hours ?? '');
      })
      .catch((e) => setError(extractErrorMessage(e)));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setSaving(true);
    try {
      const updated = await updateMyDoctorProfile({
        bio,
        qualifications,
        consultation_hours: hours,
      });
      setProfile(updated);
      setSuccess(true);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (!profile && !error) return <SkeletonBlock lines={6} />;
  if (!profile && error) return <PageError message={error} />;

  return (
    <div>
      <h1>My Profile</h1>
      {error && <p className="error-text">{error}</p>}
      {success && <p className="success-text">Profile updated.</p>}
      {profile && (
        <form className="form" onSubmit={handleSubmit}>
          <label>
            Name
            <input value={profile.full_name} disabled />
          </label>
          <label>
            Specialty
            <input value={profile.specialty} disabled />
          </label>
          <label>
            Bio
            <textarea rows={4} value={bio} onChange={(e) => setBio(e.target.value)} />
          </label>
          <label>
            Qualifications
            <input value={qualifications} onChange={(e) => setQualifications(e.target.value)} />
          </label>
          <label>
            Consultation hours
            <input value={hours} onChange={(e) => setHours(e.target.value)} placeholder="Mon-Fri 9am-5pm" />
          </label>
          <button className="btn btn-primary" type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Save changes'}
          </button>
        </form>
      )}
    </div>
  );
}
