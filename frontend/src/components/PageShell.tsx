import React from 'react';
import { Typography } from 'antd';
import '../styles/page-shell.css';

const { Title, Text } = Typography;

type PageShellProps = {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  maxWidth?: number | string;
  children: React.ReactNode;
  className?: string;
};

const PageShell: React.FC<PageShellProps> = ({
  title,
  subtitle,
  icon,
  actions,
  maxWidth = 1080,
  children,
  className,
}) => (
  <main
    className={['page-shell', className].filter(Boolean).join(' ')}
    style={{ maxWidth: typeof maxWidth === 'number' ? `${maxWidth}px` : maxWidth }}
  >
    <header className="page-shell-header">
      <div className="page-shell-heading">
        {icon && <div className="page-shell-icon">{icon}</div>}
        <div className="page-shell-title-block">
          <Title level={3} className="page-shell-title">{title}</Title>
          {subtitle && <Text type="secondary" className="page-shell-subtitle">{subtitle}</Text>}
        </div>
      </div>
      {actions && <div className="page-shell-actions">{actions}</div>}
    </header>
    <section className="page-shell-body">
      {children}
    </section>
  </main>
);

export default PageShell;
