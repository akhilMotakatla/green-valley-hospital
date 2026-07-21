interface SkeletonBlockProps {
  lines?: number;
  widths?: string[];
}

export function SkeletonBlock({ lines = 3, widths = ['80%', '60%', '90%'] }: SkeletonBlockProps) {
  return (
    <div style={{ padding: '0.5rem 0' }}>
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="skeleton-bar"
          style={{ width: widths[i % widths.length] }}
        />
      ))}
    </div>
  );
}
