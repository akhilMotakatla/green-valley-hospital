export function Pager({
  page,
  pageSize,
  total,
  totalPages: totalPagesProp,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  totalPages?: number;
  onPageChange: (page: number) => void;
}) {
  const totalPages = totalPagesProp ?? Math.max(1, Math.ceil(total / pageSize));
  if (totalPages <= 1) return null;
  return (
    <div className="pagination">
      <button className="btn btn-outline" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
        Prev
      </button>
      <span className="muted">
        Page {page} of {totalPages} ({total} total)
      </span>
      <button
        className="btn btn-outline"
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
      >
        Next
      </button>
    </div>
  );
}
