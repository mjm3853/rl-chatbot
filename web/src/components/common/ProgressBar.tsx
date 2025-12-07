import styles from './ProgressBar.module.css';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercent?: boolean;
}

export function ProgressBar({ value, max = 100, label, showPercent = true }: ProgressBarProps) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={styles.wrapper}>
      {(label || showPercent) && (
        <div className={styles.labels}>
          {label && <span className={styles.label}>{label}</span>}
          {showPercent && <span className={styles.percent}>{Math.round(percent)}%</span>}
        </div>
      )}
      <div className={styles.track}>
        <div className={styles.fill} style={{ width: `${percent}%` }} />
      </div>
    </div>
  );
}
