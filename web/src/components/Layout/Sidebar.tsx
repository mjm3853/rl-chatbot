import { NavLink } from 'react-router-dom';
import styles from './Sidebar.module.css';

const navItems = [
  { path: '/', label: 'Dashboard', icon: '◈' },
  { path: '/agents', label: 'Agents', icon: '◇' },
  { path: '/chat', label: 'Chat', icon: '◆' },
  { path: '/conversations', label: 'Conversations', icon: '◇' },
  { path: '/test-cases', label: 'Test Cases', icon: '◇' },
  { path: '/evaluations', label: 'Evaluations', icon: '◇' },
  { path: '/training', label: 'Training', icon: '◇' },
];

export function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.header}>
        <span className={styles.logo}>⬡</span>
        <span className={styles.title}>RL CHATBOT</span>
      </div>

      <nav className={styles.nav}>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `${styles.navItem} ${isActive ? styles.active : ''}`
            }
          >
            <span className={styles.icon}>{item.icon}</span>
            <span className={styles.label}>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className={styles.footer}>
        <span className={styles.version}>v0.1.0</span>
      </div>
    </aside>
  );
}
