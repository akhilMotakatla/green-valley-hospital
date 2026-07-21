// Builds an unsigned-but-well-formed JWT string good enough for jwt-decode
// to parse (AuthContext only decodes the payload client-side, it never
// verifies the signature -- that's the backend's job).
function base64url(input: string): string {
  return Buffer.from(input, 'utf-8')
    .toString('base64')
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

export function makeFakeJwt(payload: Record<string, unknown>): string {
  const header = base64url(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const body = base64url(JSON.stringify(payload));
  return `${header}.${body}.fake-signature`;
}

export function makeValidToken(overrides: Partial<{ sub: string; role: string; email: string }> = {}): string {
  const nowSeconds = Math.floor(Date.now() / 1000);
  return makeFakeJwt({
    sub: overrides.sub ?? '1',
    role: overrides.role ?? 'Patient',
    email: overrides.email ?? 'user@example.com',
    iat: nowSeconds,
    exp: nowSeconds + 3600,
  });
}
