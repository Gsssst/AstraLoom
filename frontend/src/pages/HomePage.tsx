import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Col, Input, Row, Space, Tag, Typography } from 'antd';
import {
  ArrowRightOutlined,
  BookOutlined,
  BulbOutlined,
  ClockCircleOutlined,
  CommentOutlined,
  EditOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  FileTextOutlined,
  GlobalOutlined,
  NodeIndexOutlined,
  RocketOutlined,
  SearchOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { prefetchRouteIntent } from '../routes/lazyRoutes';
import '../styles/home.css';

const { Text } = Typography;

function generateStars(count: number) {
  return Array.from({ length: count }, (_, id) => ({
    id,
    left: `${Math.random() * 100}%`,
    top: `${Math.random() * 100}%`,
    size: Math.random() * 2.8 + 1.2,
    delay: Math.random() * 4,
    duration: Math.random() * 3 + 3,
  }));
}

interface StarPoint {
  id: number;
  left: string;
  top: string;
  size: number;
  delay: number;
  duration: number;
}

function useCountUp(end: number, duration: number, startCounting: boolean) {
  const [count, setCount] = useState(0);
  const frameRef = useRef<number>(0);
  useEffect(() => {
    if (!startCounting) return;
    const startTime = performance.now();
    const animate = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      setCount(Math.floor((1 - Math.pow(1 - progress, 3)) * end));
      if (progress < 1) frameRef.current = requestAnimationFrame(animate);
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(frameRef.current);
  }, [end, duration, startCounting]);
  return count;
}

const workflowNodes = [
  { key: 'papers', label: 'Papers', detail: '检索与沉淀证据', x: 16, y: 58, icon: <BookOutlined /> },
  { key: 'ideas', label: 'Ideas', detail: '生成与迭代方向', x: 40, y: 28, icon: <BulbOutlined /> },
  { key: 'experiments', label: 'Experiments', detail: '规划实验路径', x: 64, y: 52, icon: <ExperimentOutlined /> },
  { key: 'writing', label: 'Writing', detail: '组织论文草稿', x: 84, y: 24, icon: <EditOutlined /> },
];

const featureCards = [
  {
    icon: <FileSearchOutlined />,
    title: '论文星图',
    desc: '统一检索、导入、分类和维护论文，把分散证据变成可追踪的研究资料。',
    path: '/papers',
  },
  {
    icon: <NodeIndexOutlined />,
    title: 'Idea 编织',
    desc: '从论文缺口、方法脉络和实验约束中生成可讨论、可验证的研究方案。',
    path: '/research',
  },
  {
    icon: <CommentOutlined />,
    title: 'AI 讨论室',
    desc: '用可配置模型围绕论文、项目空间和研究方向持续对话。',
    path: '/chat',
  },
  {
    icon: <FileTextOutlined />,
    title: '写作工作台',
    desc: '将证据卡片、引用和章节草稿组织成可编译、可迭代的论文项目。',
    path: '/writing',
  },
];

const quickActions = [
  { key: 'chat', icon: <CommentOutlined />, label: 'AI 对话', desc: '讨论论文和研究问题', path: '/chat' },
  { key: 'papers', icon: <BookOutlined />, label: '论文库', desc: '检索、导入、维护论文', path: '/papers' },
  { key: 'research', icon: <ExperimentOutlined />, label: '研究方向', desc: '生成和迭代 Idea', path: '/research' },
  { key: 'writing', icon: <EditOutlined />, label: '写作助手', desc: '章节写作与引用', path: '/writing' },
];

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [stars] = useState<StarPoint[]>(() => generateStars(72));
  const [searchValue, setSearchValue] = useState('');
  const [statsVisible, setStatsVisible] = useState(false);
  const statsRef = useRef<HTMLDivElement>(null);

  const paperCount = useCountUp(12860, 2000, statsVisible);
  const ideaCount = useCountUp(3847, 2400, statsVisible);
  const userCount = useCountUp(156, 1800, statsVisible);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setStatsVisible(true);
        observer.disconnect();
      }
    }, { threshold: 0.3 });
    if (statsRef.current) observer.observe(statsRef.current);
    return () => observer.disconnect();
  }, []);

  const handleSearch = useCallback(() => {
    if (searchValue.trim()) navigate(`/papers?q=${encodeURIComponent(searchValue.trim())}`);
  }, [searchValue, navigate]);

  const routeIntentProps = (path: string) => ({
    onMouseEnter: () => prefetchRouteIntent(path),
    onFocus: () => prefetchRouteIntent(path),
    onTouchStart: () => prefetchRouteIntent(path),
  });

  return (
    <div className="astraloom-home">
      <section className="astraloom-hero">
        <div className="astraloom-sky" aria-hidden="true">
          {stars.map(star => (
            <span
              key={star.id}
              className="astraloom-star"
              style={{
                left: star.left,
                top: star.top,
                width: star.size,
                height: star.size,
                animationDelay: `${star.delay}s`,
                animationDuration: `${star.duration}s`,
              }}
            />
          ))}
        </div>

        <div className="loom-stage" aria-hidden="true">
          <svg className="loom-lines" viewBox="0 0 100 70" preserveAspectRatio="none">
            <path d="M16 58 C26 32, 32 30, 40 28" />
            <path d="M40 28 C50 30, 56 48, 64 52" />
            <path d="M64 52 C72 42, 78 30, 84 24" />
            <path d="M16 58 C34 64, 56 66, 84 24" className="loom-line-muted" />
          </svg>
          {workflowNodes.map(node => (
            <div key={node.key} className="loom-node" style={{ left: `${node.x}%`, top: `${node.y}%` }}>
              <span>{node.icon}</span>
              <strong>{node.label}</strong>
              <small>{node.detail}</small>
            </div>
          ))}
        </div>

        <div className="astraloom-hero-content">
          <div className="astraloom-kicker">
            <RocketOutlined />
            <span>AI Research Workspace</span>
          </div>
          <h1 className="astraloom-title">AstraLoom</h1>
          <p className="astraloom-subtitle">
            把论文、证据、灵感和实验线索编织成一张清晰的科研星图。
          </p>

          <div className="astraloom-search">
            <Input
              size="large"
              placeholder="搜索论文，例如：multimodal reasoning, diffusion policy, RAG..."
              prefix={<SearchOutlined />}
              value={searchValue}
              onChange={event => setSearchValue(event.target.value)}
              onPressEnter={handleSearch}
              suffix={(
                <Button type="primary" shape="round" icon={<ArrowRightOutlined />} onClick={handleSearch}>
                  搜索论文
                </Button>
              )}
            />
          </div>

          <div className="astraloom-actions">
            {quickActions.map(action => (
              <button
                key={action.key}
                className="astraloom-action"
                onClick={() => navigate(action.path)}
                {...routeIntentProps(action.path)}
              >
                <span className="astraloom-action-icon">{action.icon}</span>
                <span>
                  <strong>{action.label}</strong>
                  <small>{action.desc}</small>
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      <section className="astraloom-stats" ref={statsRef}>
        <div className="astraloom-stats-grid">
          {[
            { value: paperCount.toLocaleString() + '+', label: '已收录论文', icon: <BookOutlined /> },
            { value: ideaCount.toLocaleString() + '+', label: '生成研究 Idea', icon: <BulbOutlined /> },
            { value: userCount.toLocaleString() + '+', label: '活跃课题组', icon: <TeamOutlined /> },
            { value: '24/7', label: '持续研究辅助', icon: <ClockCircleOutlined /> },
          ].map((item, index) => (
            <div key={item.label} className="astraloom-stat" style={statsVisible ? { opacity: 1, transform: 'translateY(0)', transitionDelay: `${index * 0.06}s` } : {}}>
              <span>{item.icon}</span>
              <strong>{item.value}</strong>
              <small>{item.label}</small>
            </div>
          ))}
        </div>
      </section>

      <section className="astraloom-features">
        <div className="astraloom-section-heading">
          <Tag color="geekblue">Research Flow</Tag>
          <h2>从论文线索到可写作成果</h2>
          <p>AstraLoom 让科研过程里的每一条线索都能被保存、讨论、验证和写入论文。</p>
        </div>
        <Row gutter={[18, 18]} className="astraloom-feature-grid">
          {featureCards.map(card => (
            <Col xs={24} sm={12} lg={6} key={card.title}>
              <button className="astraloom-feature-card" onClick={() => navigate(card.path)} {...routeIntentProps(card.path)}>
                <span className="astraloom-feature-icon">{card.icon}</span>
                <h3>{card.title}</h3>
                <p>{card.desc}</p>
                <Text>打开 <ArrowRightOutlined /></Text>
              </button>
            </Col>
          ))}
        </Row>
      </section>

      <footer className="astraloom-footer">
        <Space direction="vertical" size={8}>
          <div className="astraloom-footer-mark"><GlobalOutlined /> AstraLoom</div>
          <Text type="secondary">© 2026 · AI Research Workspace · Papers to ideas to manuscripts</Text>
        </Space>
      </footer>
    </div>
  );
};

export default HomePage;
