export function StatTile({ value, label, onClick, selected }: {
  value: number | string;
  label: string;
  /** Makes the tile a button, e.g. to open the list behind the number. */
  onClick?: () => void;
  selected?: boolean;
}) {
  const body = (
    <>
      <div className="value">{value}</div>
      <div className="label">{label}{onClick && ' ›'}</div>
    </>
  );
  if (!onClick) return <div className="stat">{body}</div>;
  return (
    <button type="button" className={`stat stat-btn ${selected ? 'selected' : ''}`} onClick={onClick} aria-pressed={selected}>
      {body}
    </button>
  );
}
