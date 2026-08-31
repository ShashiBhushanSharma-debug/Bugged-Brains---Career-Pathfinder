export default function ProgressRing({
  value = 0,
  size = 96,
  strokeWidth = 8,
  label,
  sublabel,
  color = 'var(--pine)',
  trackColor = 'var(--line)',
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (Math.min(Math.max(value, 0), 100) / 100) * circumference;

  return (
    <div
      style={{ position: 'relative', width: size, height: size, display: 'inline-flex' }}
      role="img"
      aria-label={`${sublabel || 'Progress'}: ${value}%`}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: 'stroke-dashoffset 0.6s var(--ease)' }}
        />
      </svg>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: size * 0.22 }}>
          {label ?? `${value}%`}
        </span>
        {sublabel && (
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 10.5,
              color: 'var(--ink-soft)',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
              marginTop: 2,
            }}
          >
            {sublabel}
          </span>
        )}
      </div>
    </div>
  );
}